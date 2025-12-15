from flask import Blueprint, current_app, request, render_template
from .imageSearchLogic import find_similar
import os 

search_image_bp = Blueprint('image_bp', __name__)

# ---------------------------------------------------------
# TÌM KIẾM ẢNH BẰNG ẢNH (UPLOAD)
# ---------------------------------------------------------
@search_image_bp.route("/search_image", methods=["GET", "POST"])
def search_image():
    if request.method == "POST":
        file = request.files.get("file")
        if not file:
            return "Không có ảnh nào được tải lên", 400

        upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file.filename)
        file.save(upload_path)

        # --- PHẦN ĐÃ SỬA ---
        # 1. Nhận về danh sách kết quả (list of dicts)
        results = find_similar(upload_path)
        
        # 2. Kiểm tra xem có kết quả không và lấy kết quả đầu tiên (Rank 1)
        if results and len(results) > 0:
            top_result = results[0] # Lấy phần tử đầu tiên
            best_match = top_result['file_name'] # Lấy tên file
            score = top_result['distance'] # Lấy điểm số
            
            return render_template(
                "search_result.html",
                query=file.filename,
                match=best_match,
                score=1-round(score, 3)
            )
        else:
            return "Không tìm thấy ảnh tương tự trong cơ sở dữ liệu", 404
        # -------------------

    return render_template("search_image.html")