from flask import Blueprint, current_app, request
from .imageSearchLogic import find_similar
import os #for psth join

image_bp = Blueprint('image_bp', __name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
# ---------------------------------------------------------
# TÌM KIẾM ẢNH BẰNG ẢNH (UPLOAD)
# ---------------------------------------------------------
@app.route("/search_image", methods=["GET", "POST"])
def search_image():
    if request.method == "POST":
        file = request.files.get("file")
        if not file:
            return "Không có ảnh nào được tải lên", 400

        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
          upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file.filename)
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