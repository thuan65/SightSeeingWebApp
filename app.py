import time
start = time.time()

from flask import (
    Flask, render_template, request, jsonify, Response, json,
    redirect, url_for, flash, session
)

from flask_login import (
    LoginManager, login_user, logout_user, login_required,
    UserMixin, current_user
)

from flask_socketio import (
    SocketIO, emit, join_room, leave_room
)

from sqlalchemy import func, or_
from sqlalchemy.orm import load_only
from sentence_transformers import util

# --- IMPORT MODELS & EXTENSIONS ---
from models import User, Post, Answer, ConversationHistory, LiveLocation, Friendship, Image
from extensions import db, bcrypt
from __init__ import create_app

import os
import socket
import traceback

# --- [QUAN TRỌNG] IMPORT MAP ROUTING ---
# Đảm bảo bạn đã có file __init__.py trong thư mục MapRouting
from MapRouting.MapRoutingRoute import MapRouting_bp
from LocationSharing import location_bp, register_socket_events as register_location_socket_events
from Messaging import messaging_bp, register_socket_events as register_messaging_socket_events


# =========================================================
# 1. KHỞI TẠO APP, SOCKETIO
# =========================================================
app = create_app()
socketio = SocketIO(app, cors_allowed_origins="*")

# =========================================================
# 2. CẤU HÌNH LOGIN MANAGER
# =========================================================
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login_bp.login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# =========================================================
# 3. ĐĂNG KÝ BLUEPRINT
# =========================================================
# Logic này kiểm tra xem Blueprint đã tồn tại trong app chưa.
# Nếu create_app() đã đăng ký rồi thì bỏ qua, nếu chưa thì đăng ký mới.
# Giúp tránh lỗi "ValueError: The name ... is already registered"

blueprint_name = MapRouting_bp.name  # Lấy tên định danh của Blueprint (ví dụ: Map_Routing_System)

if blueprint_name not in app.blueprints:
    app.register_blueprint(MapRouting_bp, url_prefix="/MapRouting")
    print(f" Đã đăng ký thành công Blueprint: {blueprint_name} tại /MapRouting")
else:
    print(f" Blueprint '{blueprint_name}' đã được đăng ký từ trước (Bỏ qua để tránh lỗi).")

# Đăng ký Blueprint LocationSharing
blueprint2_name = location_bp.name
if blueprint2_name not in app.blueprints:
    app.register_blueprint(location_bp)
    print(f" Đã đăng ký thành công Blueprint: {blueprint2_name} tại /location_sharing")
else:
    print(f" Blueprint '{blueprint2_name}' đã được đăng ký từ trước (Bỏ qua để tránh lỗi).")

blueprint3_name = messaging_bp.name
if blueprint3_name not in app.blueprints:
    app.register_blueprint(messaging_bp)
    print(f" Đã đăng ký thành công Blueprint: {blueprint3_name} tại /messaging")
else:
    print(f" Blueprint '{blueprint3_name}' đã được đăng ký từ trước (Bỏ qua để tránh lỗi).")

# Đăng ký các sự kiện SocketIO từ LocationSharing
register_location_socket_events(socketio)
# Đăng ký các sự kiện SocketIO từ Messaging
register_messaging_socket_events(socketio)

# =========================================================
# 4. CÁC ROUTE CHÍNH CỦA APP
# =========================================================

@app.route("/")
def index():
    """Trang chủ hiển thị danh sách ảnh"""
    keyword = request.args.get("q", "")

    try:
        if keyword:
            images = db.session.query(Image).filter(Image.tags.like(f"%{keyword}%")).all()
        else:
            images = db.session.query(Image).all()
        return render_template("index.html", images=images, keyword=keyword)
    except Exception as e:
        return f"Lỗi kết nối cơ sở dữ liệu: {str(e)}", 500


@app.route("/image/<int:image_id>")
def image_detail(image_id):
    """Trang chi tiết của một bức ảnh"""
    image = db.session.query(Image).filter_by(id=image_id).first()
    if not image:
        return "Ảnh không tồn tại!", 404
    return render_template("detail.html", image=image)


@app.route("/api/search")
def search():
    """API tìm kiếm ảnh (dùng cho AJAX nếu cần)"""
    keyword = request.args.get("q", "").lower()
    results = db.session.query(Image).filter(
        or_(
            func.lower(Image.tags).like(f"%{keyword}%"),
            func.lower(Image.name).like(f"%{keyword}%")
        )
    ).all()

    # Chuyển đổi đối tượng SQLAlchemy thành Dictionary
    data = [{c.name: getattr(img, c.name) for c in img.__table__.columns}
            for img in results]
    return jsonify(data)

@app.route("/friends")
def friends_page():
    """Trang bạn bè (Yêu cầu đăng nhập)"""
    if "user_id" not in session:
        return redirect("/auth/login")
    return render_template("friends.html")


# Route để render trang bản đồ bạn bè
@app.route('/friends_map')
@login_required 
def friends_map_test():
    """Render file friends_map.html"""
    return render_template('friends_map.html')


# =========================================================
# 5. KHỞI CHẠY SERVER
# =========================================================
if __name__ == "__main__":
    print("=== System Starting ===")

    end = time.time()
    print("Thời gian khởi chạy tổng:", end - start, "giây")

    #print(print(app.config["SQLALCHEMY_DATABASE_URI"]))
    print(f" Server đang chạy tại: http://localhost:5001")
    
    # Đổi port thành 5001
    socketio.run(app, host="0.0.0.0", port=5001, debug=False, use_reloader=False)