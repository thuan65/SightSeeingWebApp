# SuggestionsFeedback/feedback.py

from flask import Blueprint, request, jsonify, session as flask_session, render_template
from datetime import datetime
from Forum.toxic_filter import is_toxic
from extensions import db
import math
import requests
import time
import traceback
# Import từ DB
# from createDataBase import Image, Feedback, Session, User, UserSession
from models import Image, Feedback, User

feedback_bp = Blueprint("feedback", __name__)
# ---------------------------------------------------------
# HÀM GEOCDING (Đã thêm Debug)
# ---------------------------------------------------------

MAPS_CO_API_KEY = "6934fa9ead70c273351403whx21d101"

def geocode_address(address):
    if not address: return None

    url = "https://geocode.maps.co/search"
    search_query = address if "vietnam" in address.lower() else f"{address}, Vietnam"
    params = {'q': search_query, 'api_key': MAPS_CO_API_KEY}

    print(f"[DEBUG GEO] Gọi API: {search_query}") # <--- DEBUG

    try:
        time.sleep(1) 
        response = requests.get(url, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if data:
                result = data[0]
                print(f"[DEBUG GEO] KẾT QUẢ: Lat={result['lat']}, Lon={result['lon']}") # <--- DEBUG
                return {
                    'lat': float(result['lat']),
                    'lon': float(result['lon']),
                    'display_name': result['display_name']
                }
            else:
                print("[DEBUG GEO] API trả về kết quả rỗng (không tìm thấy địa chỉ).") # <--- DEBUG
    except Exception as e:
        print(f"❌ Geocoding Error: {e}")
        traceback.print_exc() # In chi tiết lỗi nếu có

    return None
# ---------------------------------------------------------
# HÀM TÍNH KHOẢNG CÁCH (Haversine)
# Trả về khoảng cách bằng mét
# ---------------------------------------------------------
def haversine(lat1, lon1, lat2, lon2):
    R = 6371000 # Bán kính Trái Đất bằng mét

    # Chuyển đổi từ độ sang radian
    phi_1 = math.radians(lat1)
    phi_2 = math.radians(lat2)

    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    # Công thức Haversine
    a = math.sin(delta_phi / 2.0)**2 + \
        math.cos(phi_1) * math.cos(phi_2) * \
        math.sin(delta_lambda / 2.0)**2

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c # Khoảng cách bằng mét


# ---------------------------------------------------------
# POST: Gửi feedback
# ---------------------------------------------------------
@feedback_bp.route("/feedback/<int:image_id>", methods=["POST"])
def submit_feedback(image_id):
    data = request.json

    rating = data.get("rating")
    comment = data.get("comment", "")
    user_id = data.get("user_id") or flask_session.get("user_id")

     # 1. Lấy tọa độ từ frontend
    user_lat = data.get("lat")
    user_lng = data.get("lng")

    print(f"\n[DEBUG FEEDBACK] Image ID: {image_id}, User ID: {user_id}")
    print(f"[DEBUG FEEDBACK] Tọa độ User nhận được: Lat={user_lat}, Lng={user_lng}")

    # Kiểm tra toxic
    if is_toxic(comment):
        return render_template("detail.html", error="Nội dung bình luận không phù hợp. Vui lòng viết lại.") 

    if not user_id:
        return jsonify({"error": "User not logged in"}), 401
    if rating is None:
        return jsonify({"error": "Rating is required"}), 400

    # Kiểm tra bắt buộc có tọa độ user
    if user_lat is None or user_lng is None:
        return jsonify({"error": "Vui lòng cấp quyền truy cập vị trí để đánh giá."}), 400
    
    try:
        # Tìm ảnh trong DB
        image = db.session.query(Image).filter_by(id=image_id).first()
        if not image:
            return jsonify({"error": "Image not found"}), 404
        # 2. Lấy địa chỉ của địa điểm và Geocoding 
        location_address = image.address

        print(f"[DEBUG FEEDBACK] Địa chỉ địa điểm: {location_address}") 

        if not location_address:
            # Nếu địa điểm không có địa chỉ, không có cơ sở để từ chối
            print(f"DEBUG: Địa điểm ID {id} không có địa chỉ. Bỏ qua kiểm tra vị trí.")
        else:
            # Chuyển đổi địa chỉ sang Lat/Lng
            geo_result = geocode_address(location_address)

            if not geo_result:
                print(f"DEBUG: Geocoding thất bại cho {location_address}. Bỏ qua kiểm tra vị trí.")
            else:
                image_lat = geo_result['lat']
                image_lng = geo_result['lon'] 

                # 3. Tính khoảng cách và kiểm tra (2km = 2000m)
                distance = haversine(
                    float(user_lat), float(user_lng), 
                    image_lat, image_lng
                )

                # GIỚI HẠN BÁN KÍNH
                RADIUS_KM = 2 # Đặt là 2km
                RADIUS_METER = RADIUS_KM * 1000

                print(f"[DEBUG FEEDBACK] Khoảng cách tính được: {distance:.2f} mét. Giới hạn: {RADIUS_METER} mét.")

                if distance > RADIUS_METER:
                    print(f"[DEBUG FEEDBACK] TỪ CHỐI: Khoảng cách > {RADIUS_KM} km.") # <--- DEBUG
                    return jsonify({
                        "error": f"Bạn quá xa để đánh giá. Khoảng cách: {distance:.2f} mét. Yêu cầu: dưới {RADIUS_KM} km."
                    }), 403
                else: print(f"[DEBUG FEEDBACK] CHẤP NHẬN: Khoảng cách OK.") # <--- DEBUG

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
