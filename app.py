# Back end

from flask import Flask, render_template, request, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from createDataBase import Image

app = Flask(__name__)

engine = create_engine("sqlite:///images.db")
Session = sessionmaker(bind=engine)
session = Session()

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


if __name__ == "__main__":
    app.run(debug=True)
