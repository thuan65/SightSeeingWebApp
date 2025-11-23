# from flask import Flask, render_template, request, jsonify
# import sqlite3
# from sqlalchemy import create_engine, text

# app = Flask(__name__)
# app.config['JSON_AS_ASCII'] = False

# engine = create_engine("sqlite:///feedback.db")

# @app.route("/feedback")
# def feedback_page():
#     return render_template("feedback.html")

# DB = "feedback.db"
# def connect_db():
#     return sqlite3.connect(DB)

# @app.route("/submit-feedback", methods=["POST"])
# def submit_feedback():
#     data = request.json
#     rating = int(data.get("rating"))
#     comment = data.get("comment", "")
#     place_id = int(data.get("place_id"))

#     with engine.begin() as conn:
#         # Lưu feedback
#         conn.execute(
#             text("INSERT INTO feedback (rating, comment, place_id) VALUES (:r, :c, :pid)"),
#             {"r": rating, "c": comment, "pid": place_id}
#         )

#         # Lấy rating cũ
#         place = conn.execute(
#             text("SELECT rating, rating_count FROM places WHERE id = :pid"),
#             {"pid": place_id}
#         ).fetchone()

#         old_rating = place.rating
#         count = place.rating_count

#         # Tính rating mới
#         new_rating = (old_rating * count + rating) / (count + 1)
#         new_count = count + 1

#         # Update vào DB
#         conn.execute(
#             text("UPDATE places SET rating = :nr, rating_count = :nc WHERE id = :pid"),
#             {"nr": new_rating, "nc": new_count, "pid": place_id}
#         )

#     return jsonify({"status": "success", "new_rating": new_rating})

# @app.route("/get-feedback", methods=["GET"])
# def get_feedback():
#     conn = connect_db()
#     cur = conn.cursor()
#     cur.execute("SELECT rating, comment, timestamp FROM feedback ORDER BY timestamp DESC")
#     rows = cur.fetchall()
#     conn.close()
    
#     return jsonify([
#         {"rating": r[0], "comment": r[1], "timestamp": r[2]}
#         for r in rows
#     ])

# if __name__ == "__main__":
#     app.run(debug=True)

# SuggestionsFeedback/feedback.py

# feedback.py
# feedback.py
from flask import Blueprint, request, jsonify
from datetime import datetime

# Import từ DB
from createDataBase import Image, Feedback, Session

feedback_bp = Blueprint("feedback", __name__)

# ---------------------------------------------------------
# POST: Thêm feedback cho 1 ảnh
# ---------------------------------------------------------
@feedback_bp.route("/feedback/<int:image_id>", methods=["POST"])
def submit_feedback(image_id):
    data = request.json

    rating = data.get("rating")
    comment = data.get("comment", "")

    if rating is None:
        return jsonify({"error": "rating is required"}), 400

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
            image_id=image_id,    # <-- Đã sửa đúng foreign key
            rating=rating,
            comment=comment,
            timestamp=datetime.now()
        )

        session.add(fb)
        session.commit()

        return jsonify({
            "message": "Feedback submitted",
            "new_rating": new_rating,
            "rating_count": image.rating_count
        })

    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        session.close()


# ---------------------------------------------------------
# GET: Lấy danh sách feedback của 1 ảnh
# ---------------------------------------------------------
@feedback_bp.route("/feedback/<int:image_id>", methods=["GET"])
def get_feedback(image_id):
    session = Session()

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

        result = [{
            "rating": f.rating,
            "comment": f.comment,
            "timestamp": f.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        } for f in feedback_list]

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

