# app.py

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
# 3. ĐĂNG KÝ BLUEPRINT (AN TOÀN TUYỆT ĐỐI)
# =========================================================
# Logic này kiểm tra xem Blueprint đã tồn tại trong app chưa.
# Nếu create_app() đã đăng ký rồi thì bỏ qua, nếu chưa thì đăng ký mới.
# Giúp tránh lỗi "ValueError: The name ... is already registered"

blueprint_name = MapRouting_bp.name  # Lấy tên định danh của Blueprint (ví dụ: Map_Routing_System)

if blueprint_name not in app.blueprints:
    app.register_blueprint(MapRouting_bp, url_prefix="/MapRouting")
    print(f"✅ Đã đăng ký thành công Blueprint: {blueprint_name} tại /MapRouting")
else:
    print(f"ℹ️ Blueprint '{blueprint_name}' đã được đăng ký từ trước (Bỏ qua để tránh lỗi).")


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


@app.route("/chat_ui")
def chat_ui():
    """Giao diện Chatbot"""
    return render_template("chat_ui.html")


@app.route("/friends")
def friends_page():
    """Trang bạn bè (Yêu cầu đăng nhập)"""
    if "user_id" not in session:
        return redirect("/auth/login")
    return render_template("friends.html")

# =========================================================
# 4.5. LOCATION SHARING
# =========================================================

# ---------------------------------------------------------
# CORE LOGIC: CHIA SẺ VỊ TRÍ (Được di chuyển từ utils.py)
# ---------------------------------------------------------

def get_friends_ids(user_id):
    """Trả về danh sách ID bạn bè của người dùng (hai chiều)."""
    
    friendships = db.session.query(Friendship).filter(
        or_(Friendship.user_id == user_id, Friendship.friend_id == user_id)
    ).all()

    friend_ids = set()
    
    for friendship in friendships:
        if friendship.user_id != user_id:
            friend_ids.add(friendship.user_id)
        if friendship.friend_id != user_id:
            friend_ids.add(friendship.friend_id)
            
    final_ids = list(friend_ids)
    # # Lấy thông tin User của các ID bạn bè đang online
    # online_frs = User.query.filter(
    #     User.id.in_(final_ids),
    #     User.online == True
    # ).all()

    # online_friends = set()
    # for fr in online_frs:
    #     if fr.user_id != user_id:
    #         online_friends.add(fr.user_id)
    #     if fr.friend_id != user_id:
    #         online_friends.add(fr.friend_id)
    
    # realfinal_ids = list(online_friends)
    print(f"\n[DEBUG CORE] Tìm bạn bè cho ID {user_id}. Kết quả: {final_ids}")
    
    return final_ids

# ---------------------------------------------------------
# SOCKET HANDLERS (Được di chuyển từ socket_events.py)
# ---------------------------------------------------------

@socketio.on('connect')
def handle_connect():
    print(f"\n[DEBUG SOCKET] FUNC CALLED: Bắt đầu xử lý CONNECT.") 
    
    if current_user.is_authenticated:
        user_id = current_user.id
        print(f"[DEBUG CONNECT] User {current_user.username} (ID: {user_id}) ĐÃ KẾT NỐI.")
        try:
            with db.session.no_autoflush:
                user = db.session.query(User).filter_by(id=user_id).first()
                if user:
                    user.online = True
                    db.session.commit()
                    
                    room_name = f'user_{user_id}'
                    join_room(room_name)
                    print(f"[DEBUG CONNECT] DB commit OK. User {user_id} đã tham gia phòng: {room_name}")
                 
        except Exception as e:
            print(f"[DEBUG CONNECT] 🚨 LỖI DB trong connect: {e}")
            traceback.print_exc()

@socketio.on('disconnect')
def handle_disconnect():
    print(f"\n[DEBUG SOCKET] FUNC CALLED: Bắt đầu xử lý DISCONNECT.")
    if current_user.is_authenticated:
        # user_id = current_user.id
        # username = current_user.username
        try:
            with db.session.no_autoflush:
                user = db.session.query(User).filter_by(id=current_user.id).first()
                if user:
                    user.online = False
                    db.session.commit()
                    print(f"[DEBUG DISCONNECT] Cập nhật User.online = False cho ID: {user.id}")

                    # # 2. Lấy danh sách bạn bè online và thông báo cho họ
                    # # Lấy danh sách các đối tượng User của bạn bè đang online
                    # online_friends = get_friends_ids(user_id)
                    
                    # # 3. Gửi thông báo 'friend:disconnected' đến từng người bạn online
                    # for friend in online_friends:
                    #     # Gửi sự kiện 'friend:disconnected' đến room của người bạn
                    #     friend_room = str(friend.id)
                    #     emit('friend:disconnected', 
                    #         {'userId': user_id}, # Chỉ cần gửi ID của người ngắt kết nối
                    #         room=friend_room)

                    # print(f"[DEBUG DISCONNECT] Đã thông báo ngắt kết nối cho bạn bè của User ID: {user_id}")
        except Exception as e:
            print(f"[DEBUG DISCONNECT] 🚨 LỖI DB trong disconnect: {e}")
            traceback.print_exc()

@socketio.on('update_location')
def handle_update_location(data):
    print(f"\n[DEBUG SOCKET] FUNC CALLED: Bắt đầu xử lý update vị trí.") 

    if not current_user.is_authenticated:
        print("[DEBUG SOCKET] WARNING: Update từ user chưa đăng nhập bị bỏ qua.")
        return
        
    user_id = current_user.id
    
    try:
        with db.session.no_autoflush:
            # Tải lại đối tượng User an toàn
            user = db.session.query(User).options(
                load_only(User.id, User.username, User.share_mode)
            ).filter_by(id=user_id).first() 

            if not user:
                print(f"[DEBUG SOCKET] CẢNH BÁO: User ID {user_id} không tìm thấy trong DB.")
                return

            print(f"[DEBUG SOCKET] BƯỚC 1: User object tải thành công. Username: {user.username}")

            # CẬP NHẬT LIVE LOCATION
            location = db.session.query(LiveLocation).filter_by(user_id=user_id).first()
            
            if location:
                location.lat = data.get('lat')
                location.lng = data.get('lng')
            else:
                location = LiveLocation(user_id=user_id, lat=data.get('lat'), lng=data.get('lng'))
                db.session.add(location)
                
            db.session.commit()
            print(f"[DEBUG SOCKET] BƯỚC 2: DB Commit LiveLocation thành công.")

            # EMIT DỮ LIỆU
            friend_ids = get_friends_ids(user_id)
            share_mode_val = user.share_mode if user.share_mode else "friends" 
            
            location_data = {
                "user_id": user_id,
                "username": user.username,
                "lat": data.get('lat'),
                "lng": data.get('lng'),
                "share_mode": share_mode_val
            }
            
            print(f"[DEBUG SOCKET] BƯỚC 3: Chuẩn bị gửi vị trí của {user.username} đến {len(friend_ids)} người bạn. IDs: {friend_ids}")

            for friend_id in friend_ids:
                room_name = f'user_{friend_id}'
                
                if share_mode_val == 'friends': 
                    print(f"[DEBUG SOCKET] Gửi vị trí đến Room: {room_name}")
                    socketio.emit('friend_location_update', location_data, room=room_name)
                else:
                    print(f"[DEBUG SOCKET] Bỏ qua gửi vị trí đến Room: {room_name} vì share_mode là {share_mode_val}")
        
    except Exception as e:
        print(f"\n\n🚨🚨🚨 LỖI CRITICAL TRONG handle_update_location 🚨🚨🚨")
        print(f"LỖI: {e}")
        traceback.print_exc()
        print(f"🚨🚨🚨 KẾT THÚC LỖI 🚨🚨🚨\n")


# ---------------------------------------------------------
# ROUTES HTTP (Được di chuyển từ routes.py)
# ---------------------------------------------------------

# Route để render trang bản đồ bạn bè
@app.route('/friends_map')
@login_required 
def friends_map_test():
    """Render file friends_map.html"""
    return render_template('friends_map.html')

# Route API để lấy danh sách ID của bạn bè
@app.route('/api/friends_list', methods=['GET'])
@login_required
def get_friends_list_api():
    user_id = current_user.id
    friends_ids = get_friends_ids(user_id)
    print(f"[DEBUG ROUTES] API /api/friends_list trả về ID: {friends_ids}")
    return jsonify({"friends_ids": friends_ids}), 200

# Route API để JavaScript lấy thông tin người dùng (Đã có trong app.py)
@app.route('/api/current_user_info')
@login_required 
def get_current_user_info():
    """Cung cấp user_id và username cho JavaScript."""
    return jsonify({
        'user_id': current_user.id,
        'username': current_user.username,
        'share_mode': current_user.share_mode 
    })







# =========================================================
# 5. KHỞI CHẠY SERVER
# =========================================================
if __name__ == "__main__":
    print("=== System Starting ===")

    # Tạo context để đảm bảo truy cập được DB
    with app.app_context():
        # db.create_all()  # Uncomment nếu bạn muốn tạo bảng mới (cẩn thận mất dữ liệu cũ)
        pass

    print(f"🚀 Server đang chạy tại: http://localhost:5000")
    print(f"🗺️  MapRouting module tại: http://localhost:5000/MapRouting/")

    # app.run(debug=True, use_reloader=False)
    socketio.run(app, debug=True, use_reloader=False)