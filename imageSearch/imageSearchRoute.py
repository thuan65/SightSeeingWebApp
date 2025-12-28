from flask import Blueprint, current_app, request, jsonify, render_template
from models import Image
from .imageSearchLogic import find_similar
import os, json

search_image_bp = Blueprint('image_bp', __name__)

@search_image_bp.route("/search_image", methods=["GET", "POST"])
def search_image():
    if request.method == "POST":
        file = request.files.get("file")
        if not file:
            return "Không có ảnh nào được tải lên", 400

        upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file.filename)
        file.save(upload_path)

        # 1.list of dicts here
        faiss_results  = find_similar(upload_path)
        if not faiss_results:
            return jsonify([])

        #image_id
        image_ids = [item["image_id"] for item in faiss_results]

        #Query DB by img id
        images = Image.query.filter(Image.id.in_(image_ids)).all()
        image_map = {img.id: img for img in images}

        final_results = [
            {
                #**item,                          # rank, distance, image_id
                **image_map[item["image_id"]].to_dict()
            }
            for item in faiss_results
            if item["image_id"] in image_map
        ]

        return jsonify(final_results)

    return jsonify([])
