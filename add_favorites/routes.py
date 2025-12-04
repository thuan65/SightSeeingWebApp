from flask import Blueprint, request, jsonify, url_for, redirect, session, render_template
#from createDataBase import Favorite, Image, UserSession
from extensions import db
from models import Favorite, Image

favorite_bp = Blueprint(
    "favorite_bp",
    __name__,
    url_prefix="/favorite",
    template_folder="htmltemplates"
)



@favorite_bp.post("/<int:image_id>")
def add_favorite(image_id):
    if "user_id" not in session:
        return jsonify({
            "error": "Bạn chưa đăng nhập",
            "login_url": url_for("login", next=url_for("image_detail", image_id=image_id))
        }), 401

    user_id = session["user_id"]

    try:
        exists = Favorite.query.filter_by(user_id=user_id, image_id=image_id).first()
        if exists:
            return jsonify({"error": "Đã có trong danh sách yêu thích"}), 400

        fav = Favorite(user_id=user_id, image_id=image_id)
        db.session.add(fav)
        db.session.commit()
        return jsonify({"message": "ok"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@favorite_bp.get("/list")
def list_favorites():
    if "user_id" not in session:
        return redirect(url_for("login", next=url_for("favorite_bp.list_favorites")))

    user_id = session["user_id"]
    favs = db.session.query(Favorite).filter_by(user_id=user_id).all()
    img_ids = [f.image_id for f in favs]

    images = db.session.query(Image).filter(Image.id.in_(img_ids)).all()

    return render_template("favorites.html", images=images)




@favorite_bp.delete("/remove/<int:image_id>")
def remove_favorite(image_id):
    if "user_id" not in session:
        return jsonify({"error": "Chưa login"}), 401

    user_id = session["user_id"]

    try:
        fav = db.session.query(Favorite).filter_by(user_id=user_id, image_id=image_id).first()
        if not fav:
            return jsonify({"error": "Không tìm thấy favorite"}), 404

        db.session.delete(fav)
        db.session.commit()
        return jsonify({"message": "ok"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
