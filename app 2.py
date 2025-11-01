from flask import Flask, json, request, jsonify, Response
from sentence_transformers import SentenceTransformer, util
from sqlalchemy import create_engine, text
import torch

app = Flask(__name__)

app.config['JSON_AS_ASCII'] = False


# Kết nối tới database SQLite
engine = create_engine("sqlite:///places.db")

@app.route("/search_filter", methods=["GET"])
def search_filter():
    city = request.args.get("city", "")
    tag = request.args.get("tag", "")
    min_rating = float(request.args.get("rating", 0))

    query = "SELECT * FROM places WHERE 1=1"
    params = {}

    if city:
        query += " AND city LIKE :city"
        params["city"] = f"%{city}%"

    if tag:
        query += " AND tags LIKE :tag"
        params["tag"] = f"%{tag}%"

    query += " AND rating >= :min_rating"
    params["min_rating"] = min_rating

    with engine.connect() as conn:
        results = conn.execute(text(query), params).mappings().all()

    response = json.dumps([dict(row) for row in results], ensure_ascii=False)
    return Response(response, content_type="application/json; charset=utf-8")

model = SentenceTransformer("keepitreal/vietnamese-sbert")
@app.route("/search_text", methods =["GET"])
def search_text():
    query_text = request.args.get("query", "")
    if not query_text:
        return jsonify([])

    # B1: mã hóa câu người dùng nhập thành vector
    query_embedding = model.encode(query_text, convert_to_tensor=True)

    # B2: Lấy toàn bộ địa điểm trong DB
    with engine.connect() as conn:
        results = conn.execute(text("SELECT * FROM places")).mappings().all()

    # B3: So sánh độ tương đồng giữa query và mô tả từng địa điểm
    scored = []
    for r in results:
        place_embedding = model.encode(r["description"], convert_to_tensor=True)
        similarity = util.cos_sim(query_embedding, place_embedding).item()
        scored.append((similarity, r))

    # B4: Sắp xếp theo độ tương đồng cao nhất
    scored.sort(reverse=True, key=lambda x: x[0])
    top_results = [dict(x[1]) for x in scored[:2]]

    response = json.dumps(top_results, ensure_ascii=False)
    return Response(response, content_type="application/json; charset=utf-8")


if __name__ == "__main__":
    app.run(debug=True)