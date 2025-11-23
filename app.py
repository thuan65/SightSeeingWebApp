# Back end

from flask import Flask, render_template, request, jsonify, Response, json
from sentence_transformers import SentenceTransformer, util
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from chatBot import chatbot_reply
from createDataBase import Image
import torch
from flask import Flask
from feedback import feedback_bp   

app = Flask(__name__)

# Đăng ký API feedback
app.register_blueprint(feedback_bp)

app.config['JSON_AS_ASCII'] = False
engine = create_engine("sqlite:///images.db")
Session = sessionmaker(bind=engine)
session = Session()
# Kết nối tới database SQLite
#engine = create_engine("sqlite:///images.db")

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

    query = "SELECT * FROM images WHERE 1=1"
    params = {}

    if city:
        query += " AND city LIKE :city"
        params["city"] = f"%{city}%"

    if tag:
        query += " AND tags LIKE :tag"
        params["tag"] = f"%{tag}%"

    query += " AND rating >= :min_rating"
    params["min_rating"] = min_rating

    print(query)

    with engine.connect() as conn:
        results = conn.execute(text(query), params).mappings().all()

    response = json.dumps([dict(row) for row in results], ensure_ascii=False)

    for row in results:
        r = dict(row)
        print(f"- ID: {r.get('id')}, Name: {r.get('name')}, Image: {r.get('filename') or r.get('image')}, Rating: {r.get('rating')}")


    return Response(response, content_type="application/json; charset=utf-8")

# Load mô hình Sentence-BERT tiếng Việt
model = SentenceTransformer("keepitreal/vietnamese-sbert")

def get_all_places():
    """Lấy toàn bộ dữ liệu địa điểm từ database"""
    with engine.connect() as conn:
        results = conn.execute(text("SELECT * FROM images")).mappings().all()
    return results

def compute_similarity(query_text, places, top_k=5):
    """So sánh độ tương đồng giữa query và description trong DB"""

    # Encode câu người dùng nhập
    query_embedding = model.encode(query_text, convert_to_tensor=True)

    scored = []
    for place in places:
        place_embedding = model.encode(place["description"], convert_to_tensor=True)
        similarity = util.cos_sim(query_embedding, place_embedding).item()
        scored.append((similarity, place))

    # Sắp xếp theo similarity giảm dần
    scored.sort(reverse=True, key=lambda x: x[0])

    # Chỉ trả về top_k
    return [dict(x[1]) for x in scored[:top_k]]

@app.route("/search_text", methods=["GET"])
def search_text(user_messange):
    """Search theo câu nhập từ người dùng"""
    if not user_messange.strip():
        return jsonify([])

    places = get_all_places()
    top_results = compute_similarity(user_messange, places)

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
