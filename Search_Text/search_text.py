from flask import Blueprint, request, Response, jsonify
from sentence_transformers import util
from sqlalchemy import create_engine, text
from models_loader import sbert_model
import json
import os

# --- Khởi tạo tài nguyên ---

# 1. Định nghĩa Blueprint
search_text = Blueprint("search_text", __name__)

# 2. Khởi tạo SentenceTransformer Model
# Sử dụng mô hình tiếng Việt đã được nhắc đến

# 3. Kết nối Database Engine
def get_db_engine():
    """
    Tạo và trả về SQLAlchemy Engine để kết nối tới images.db.
    Lưu ý: Engine này phải đồng nhất với cấu hình trong createDataBase.py
    (đã giả định là sqlite:///images.db).
    """
    return create_engine("sqlite:///images.db", echo=False)

# --- Logic Xử lý Dữ liệu ---

def get_all_places():
    """Lấy tất cả địa điểm (images) từ database."""
    # Lấy engine đã kết nối tới images.db
    engine = get_db_engine()
    with engine.connect() as conn:
        results = conn.execute(text("SELECT * FROM images")).mappings().all()
    # Chuyển đổi kết quả (Mapping) sang danh sách các dict Python
    return [dict(row) for row in results]

def compute_similarity(query_text, places, top_k=5):
    """Tính toán độ tương đồng cosine giữa truy vấn và mô tả địa điểm."""
    # Kiểm tra nếu mô hình chưa được tải (xử lý lỗi)
    if not hasattr(sbert_model, 'encode'):
        print("Error: SBERT model is not ready. Returning empty results.")
        return []

    query_embedding = sbert_model.encode(query_text, convert_to_tensor=True)
    scored = []
    
    for place in places:
        # Sử dụng trường 'description' để tính độ tương đồng
        description_text = place.get("description", "")
        
        # Nếu description quá ngắn hoặc trống, bỏ qua hoặc gán similarity thấp
        if not description_text or len(description_text.split()) < 3:
             similarity = 0.0
        else:
            place_embedding = sbert_model.encode(description_text, convert_to_tensor=True)
            similarity = util.cos_sim(query_embedding, place_embedding).item()
        
        scored.append((similarity, place))
        
    # Sắp xếp giảm dần theo similarity
    scored.sort(reverse=True, key=lambda x: x[0])
    # Trả về top_k kết quả
    return [dict(x[1]) for x in scored[:top_k]]

# --- Route API ---

@search_text.route("/search_text", methods=["GET"])
def search_text_route():
    """Endpoint tìm kiếm địa điểm dựa trên ngữ nghĩa (Semantic Search)."""
    user_message = request.args.get("query", "").strip()
    # Kiểm tra đầu vào
    if not user_message:
        return jsonify({"message": "Vui lòng nhập từ khóa tìm kiếm."})

    try:
        # 1. Lấy tất cả địa điểm từ DB
        places = get_all_places()

        # 2. Tính toán độ tương đồng ngữ nghĩa
        top_results = compute_similarity(user_message, places)
        
        # 3. Trả về kết quả JSON
        response = json.dumps(top_results, ensure_ascii=False)
        return Response(response, content_type="application/json; charset=utf-8")
    
    except Exception as e:
        print(f"Lỗi khi thực hiện tìm kiếm ngữ nghĩa: {e}")
        error_response = json.dumps({"error": "Đã xảy ra lỗi hệ thống khi tìm kiếm ngữ nghĩa."}, ensure_ascii=False)
        return Response(error_response, status=500, content_type="application/json; charset=utf-8")