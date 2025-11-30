from flask import Blueprint, request, Response
from sqlalchemy import create_engine, text
import json
import os

# --- Thiết lập Engine (Đọc từ cấu hình trong createDataBase.py) ---

def get_db_engine():
    """
    Tạo và trả về SQLAlchemy Engine để kết nối tới images.db.
    Lưu ý: Bạn phải đảm bảo rằng engine này được tạo đồng nhất với
    cấu hình trong createDataBase.py (sqlite:///images.db).
    """
    # Vì file images.db được tạo ở thư mục gốc, ta sử dụng đường dẫn tương đối này.
    # Trong môi trường sản xuất/lớn hơn, bạn nên dùng biến môi trường để định nghĩa đường dẫn DB.
    
    # Giả sử images.db nằm ở thư mục gốc của ứng dụng
    return create_engine("sqlite:///images.db", echo=False)

# --- Định nghĩa Blueprint ---

search_filter = Blueprint("search_filter", __name__)

@search_filter.route("/search_filter", methods=["GET"])
def search_filter_route():
    try:
        # Lấy tham số từ request
        city = request.args.get("city", "").strip()
        tag = request.args.get("tag", "").strip()
        
        # Xử lý rating, đảm bảo là float hợp lệ, nếu không thì mặc định là 0
        min_rating_str = request.args.get("rating", "0").strip()
        try:
            min_rating = float(min_rating_str)
        except ValueError:
            min_rating = 0.0 # Mặc định nếu không phải số

        # --- Xây dựng Query Động ---
        query = "SELECT * FROM images WHERE 1=1"
        params = {}

        if city:
            query += " AND name LIKE :city OR description LIKE :city" # Thêm điều kiện tìm kiếm trong tên và mô tả
            params["city"] = f"%{city}%"
            
        if tag:
            query += " AND tags LIKE :tag"
            params["tag"] = f"%{tag}%"
            
        # Thêm điều kiện Rating
        query += " AND rating >= :min_rating"
        params["min_rating"] = min_rating
        
        # Tùy chọn: Sắp xếp kết quả theo rating giảm dần
        query += " ORDER BY rating DESC, rating_count DESC"
        
        engine = get_db_engine()
        with engine.connect() as conn:
            # Thực thi query
            results = conn.execute(text(query), params).mappings().all()

        # Chuyển kết quả về định dạng JSON
        # Chuyển đổi mỗi row (mapping) thành dictionary để dễ dàng serialize
        data = [dict(row) for row in results]
        
        # Trả về Response
        response_data = json.dumps(data, ensure_ascii=False)
        return Response(response_data, content_type="application/json; charset=utf-8")
        
    except Exception as e:
        # Xử lý lỗi chung (Ví dụ: lỗi DB, lỗi cấu hình)
        print(f"Lỗi khi thực hiện tìm kiếm: {e}")
        error_response = json.dumps({"error": "Đã xảy ra lỗi hệ thống khi tìm kiếm."}, ensure_ascii=False)
        return Response(error_response, status=500, content_type="application/json; charset=utf-8")