from flask import Blueprint, request, Response, jsonify, current_app
from sentence_transformers import util
from sqlalchemy import create_engine, text
from models import Image
from extensions import db
from models_loader import sbert_model
import faiss
import faiss_loader
import json
import os

# --- Khởi tạo tài nguyên ---

# 1. Định nghĩa Blueprint
search_text = Blueprint("search_text", __name__)

# 2. Khởi tạo SentenceTransformer Model
# Sử dụng mô hình tiếng Việt đã được nhắc đến

# 3. Kết nối Database Engine
# def get_db_engine():
#     """
#     Tạo và trả về SQLAlchemy Engine để kết nối tới images.db.
#     Lưu ý: Engine này phải đồng nhất với cấu hình trong createDataBase.py
#     (đã giả định là sqlite:///images.db).
#     """
#     return create_engine("sqlite:///instance/images.db", echo=False)

# --- Logic Xử lý Dữ liệu ---

def get_all_places():
    """Lấy tất cả địa điểm (images) từ database."""
    # Lấy engine đã kết nối tới images.db
    # engine = get_db_engine()
    with current_app.app_context() as conn:
        results = db.session.execute(db.text("SELECT * FROM images")).mappings().all()
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

# ======================================================
# FUNCTION HELPER
# ======================================================
# Trả về danh sách ID địa điểm giống trên một tiêu chí nhất định
def threshold_search(query_emb):
    top_k = 50
    threshold = 0.25
    distances, indices = faiss_loader.faiss_Text_index.search(query_emb, top_k)
    results = [
        {"id": idx, "similarity": score}
        for idx, score in zip(indices[0], distances[0])
        if score >= threshold
]
    return results
# ======================================================

def to_dict(model):
    return {
        c.name: getattr(model, c.name)
        for c in model.__table__.columns
    }
# ======================================================

# --- Route API ---

@search_text.route("/search_text", methods=["GET"])
def search_text_route():
    # Endpoint tìm kiếm địa điểm dựa trên ngữ nghĩa (Semantic Search)
    user_message = request.args.get("query", "").strip()
    # Kiểm tra đầu vào
    if not user_message:
        return jsonify({"message": "Vui lòng nhập từ khóa tìm kiếm."}), 400

    if not hasattr(sbert_model, "encode"):
        return jsonify({"error": "Model chưa sẵn sàng"}), 503

    query_emb = sbert_model.encode([user_message], convert_to_numpy=True)
    query_emb = query_emb.astype('float32')
    faiss.normalize_L2(query_emb)  # nếu index đã normalize

    try:
        topK_Similarity_List = threshold_search(query_emb)
        faiss_indices = [item["id"] for item in topK_Similarity_List] # Lấy các index từ trong vector embedding
        image_ids = [faiss_loader.index_to_image_id[idx] for idx in faiss_indices if idx in faiss_loader.index_to_image_id]# Đởi mapping idex sang id trong database

        results = [] 

        if not image_ids:
            return jsonify([])   
        #Query Database
        images = Image.query.filter(Image.id.in_(image_ids)).all()
        if images: # Nếu image có tồn tại
            results = [to_dict(img) for img in images if img in images]
# 3. Trả về kết quả JSON
        return jsonify(results)
    except Exception as e:
        print(f"Lỗi khi thực hiện tìm kiếm ngữ nghĩa: {e}")
        return jsonify({"error": "Đã xảy ra lỗi hệ thống"}), 500

# def search_text_route():
#     """Endpoint tìm kiếm địa điểm dựa trên ngữ nghĩa (Semantic Search)."""
#     user_message = request.args.get("query", "").strip()
#     print(user_message)
#     # Kiểm tra đầu vào
#     if not user_message:
#         return jsonify({"message": "Vui lòng nhập từ khóa tìm kiếm."})

#     try:
#         # 1. Lấy tất cả địa điểm từ DB
#         places = get_all_places()

#         # 2. Tính toán độ tương đồng ngữ nghĩa
#         top_results = compute_similarity(user_message, places)
        
#         # 3. Trả về kết quả JSON
#         response = json.dumps(top_results, ensure_ascii=False)
#         return Response(response, content_type="application/json; charset=utf-8")
    
    # except Exception as e:
    #     print(f"Lỗi khi thực hiện tìm kiếm ngữ nghĩa: {e}")
    #     error_response = json.dumps({"error": "Đã xảy ra lỗi hệ thống khi tìm kiếm ngữ nghĩa."}, ensure_ascii=False)
    #     return Response(error_response, status=500, content_type="application/json; charset=utf-8")