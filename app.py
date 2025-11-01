# Back end

from flask import Flask, render_template, request, jsonify, Response, json
from sentence_transformers import SentenceTransformer, util
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from chatBot import chatbot_reply
from createDataBase import Image
from chatBot import chatbot_reply
import torch

app = Flask(__name__)

app.config['JSON_AS_ASCII'] = False
engine = create_engine("sqlite:///images.db")
Session = sessionmaker(bind=engine)
session = Session()
# Kết nối tới database SQLite
engine = create_engine("sqlite:///places.db")

@app.route("/")
def index():
    keyword = request.args.get("q", "")
    if keyword:
        images = session.query(Image).filter(Image.tags.like(f"%{keyword}%")).all()
    else:
        images = session.query(Image).all()
    return render_template("index.html", images=images, keyword=keyword)

@app.route("/image/<int:image_id>")
def image_detail(image_id):
    image = session.query(Image).filter_by(id=image_id).first()
    if not image:
        return "Ảnh không tồn tại!", 404
    return render_template("detail.html", image=image)

@app.route("/api/search")
def search():
    keyword = request.args.get("q", "").lower()
    session = Session()

    results = session.query(Image).filter(Image.tags.like(f"%{keyword}%")).all()
    data = [{"id": img.id, "name": img.name, "filename": img.filename} for img in results]
    return jsonify(data)

# NEW CODE: để người dùng upload ảnh 
import os
from Search_Imagine import find_similar  # import hàm AI tìm ảnh tương tự

app.config['UPLOAD_FOLDER'] = 'static/uploads'

@app.route("/search_image", methods=["GET", "POST"])
def search_image():
    if request.method == "POST":
        file = request.files.get("file")
        if not file:
            return "Không có ảnh nào được tải lên", 400

        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(upload_path)

        # Gọi hàm tìm ảnh tương tự
        best_match, score = find_similar(upload_path)

        return render_template(
            "search_result.html",
            query=file.filename,
            match=best_match,
            score=round(score, 3)
        )

    return render_template("search_image.html")

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

@app.route("/map")
def show_map():
    return render_template("map.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    if not data or "message" not in data:
        return jsonify({"error": "Missing 'message' in request"}), 400

    user_message = data["message"].strip()
    if not user_message:
        return jsonify({"error": "Empty message"}), 400

    try:
        bot_response = chatbot_reply(user_message)
        return jsonify({"reply": bot_response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route("/chat_ui")
def chat_ui():
    return render_template("chat_ui.html")

if __name__ == "__main__":
    app.run(debug=True)
