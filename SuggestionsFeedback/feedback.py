# SuggestionsFeedback/feedback.py

from flask import Blueprint, request, jsonify, session as flask_session, render_template
from Forum.toxic_filter import is_toxic
from datetime import datetime

# Import từ DB
from createDataBase import Image, Feedback, Session, User, UserSession

feedback_bp = Blueprint("feedback", __name__)

# ---------------------------------------------------------
# POST: Thêm feedback cho 1 ảnh
# ---------------------------------------------------------
@feedback_bp.route("/feedback/<int:image_id>", methods=["POST"])
def submit_feedback(image_id):
    
    data = request.json

    print("DATA:", data)
    print("USER_ID:", data.get("user_id"))

    rating = data.get("rating")
    comment = data.get("comment", "")
    user_id = data.get("user_id") or flask_session.get("user_id")

    if is_toxic(comment):
        return render_template("detail.html", error="Nội dung bình luận không phù hợp. Vui lòng viết lại.") 
    if not user_id:
        return jsonify({"error": "User not logged in"}), 401
    if rating is None:
        return jsonify({"error": "Rating is required"}), 400

    session = Session()

    try:
        # Tìm ảnh trong DB
        image = session.query(Image).filter_by(id=image_id).first()
        if not image:
            return jsonify({"error": "Image not found"}), 404

        # Tính rating mới
        old_rating = image.rating or 0
        old_count = image.rating_count or 0
        new_rating = (old_rating * old_count + rating) / (old_count + 1)

        image.rating = new_rating
        image.rating_count = old_count + 1

        # Thêm feedback mới
        fb = Feedback(
            user_id=user_id,
            image_id=image_id,
            rating=rating,
            comment=comment,
            timestamp=datetime.now()
        )

        session.add(fb)
        session.commit()

        return jsonify({
            "message": "Feedback submitted",
            "user_id": fb.user_id,
            "new_rating": new_rating,
            "rating_count": image.rating_count,
        })

    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        session.close()


# ---------------------------------------------------------
# GET: Lấy danh sách feedback của 1 ảnh kèm username
# ---------------------------------------------------------
@feedback_bp.route("/feedback/<int:image_id>", methods=["GET"])
def get_feedback(image_id):
    session = Session()
    usession = UserSession()

    try:
        image = session.query(Image).filter_by(id=image_id).first()
        if not image:
            return jsonify({"error": "Image not found"}), 404

        feedback_list = (
            session.query(Feedback)
            .filter_by(image_id=image_id)
            .order_by(Feedback.timestamp.desc())
            .all()
        )

        result = []
        for f in feedback_list:
            # Lấy username từ users.db
            user = usession.query(User).filter_by(id=f.user_id).first()
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

    finally:
        session.close()
        usession.close()
