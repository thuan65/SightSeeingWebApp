# SuggestionsFeedback/feedback.py

from flask import Blueprint, request, jsonify, session as flask_session, render_template
from datetime import datetime
from Forum.toxic_filter import is_toxic
from extensions import db


# Import từ DB
# from createDataBase import Image, Feedback, Session, User, UserSession
from models import Image, Feedback, User

feedback_bp = Blueprint("feedback", __name__)


# ---------------------------------------------------------
# POST: Gửi feedback
# ---------------------------------------------------------
@feedback_bp.route("/feedback/<int:image_id>", methods=["POST"])
def submit_feedback(image_id):
    data = request.json

    rating = data.get("rating")
    comment = data.get("comment", "")
    user_id = data.get("user_id") or flask_session.get("user_id")

    # Kiểm tra toxic
    if is_toxic(comment):
        return render_template("detail.html", error="Nội dung bình luận không phù hợp. Vui lòng viết lại.") 

    if not user_id:
        return jsonify({"error": "User not logged in"}), 401
    if rating is None:
        return jsonify({"error": "Rating is required"}), 400


    try:
        # Tìm ảnh trong DB
        image = db.session.query(Image).filter_by(id=image_id).first()
        if not image:
            return jsonify({"error": "Image not found"}), 404

        # Update rating
        old_rating = image.rating or 0
        old_count = image.rating_count or 0
        new_rating = (old_rating * old_count + rating) / (old_count + 1)

        image.rating = new_rating
        image.rating_count = old_count + 1

        fb = Feedback(
            user_id=user_id,
            image_id=image_id,
            rating=rating,
            comment=comment,
            timestamp=datetime.now()
        )

        db.session.add(fb)
        db.session.commit()

        return jsonify({
            "message": "Feedback submitted",
            "user_id": fb.user_id,
            "new_rating": new_rating,
            "rating_count": image.rating_count,
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------
# GET: Lấy feedback + username
# ---------------------------------------------------------
@feedback_bp.route("/feedback/<int:image_id>", methods=["GET"])
def get_feedback(image_id):
  

    try:
        image = db.session.query(Image).filter_by(id=image_id).first()
        if not image:
            return jsonify({"error": "Image not found"}), 404

        feedback_list = (
            db.session.query(Feedback)
            .filter_by(image_id=image_id)
            .order_by(Feedback.timestamp.desc())
            .all()
        )

        result = []
        for f in feedback_list:
            # Lấy username từ users.db
            user = db.session.query(User).filter_by(id=f.user_id).first()
            username = user.username if user else "Unknown"

            result.append({
                "user_id": f.user_id,
                "username": username,
                "rating": f.rating,
                "comment": f.comment,
                "timestamp": f.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            })

        return jsonify({
            "image_id": image_id,
            "average_rating": image.rating,
            "rating_count": image.rating_count,
            "feedback": result
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
