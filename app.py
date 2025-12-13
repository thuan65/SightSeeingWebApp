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
from LocationSharing import location_bp, register_socket_events

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

blueprint2_name = location_bp.name
if blueprint2_name not in app.blueprints:
    app.register_blueprint(location_bp)
    print(f"✅ Đã đăng ký thành công Blueprint: {blueprint2_name} tại /location_sharing")
else:
    print(f"ℹ️ Blueprint '{blueprint2_name}' đã được đăng ký từ trước (Bỏ qua để tránh lỗi).")

# Đăng ký các sự kiện SocketIO từ LocationSharing
register_socket_events(socketio)

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

# def get_friends_ids(user_id):
#     """Trả về danh sách ID bạn bè của người dùng (hai chiều)."""
    
#     friendships = db.session.query(Friendship).filter(
#         or_(Friendship.user_id == user_id, Friendship.friend_id == user_id)
#     ).all()

#     friend_ids = set()
    
#     for friendship in friendships:
#         # if (friendship.user_id != user_id):
#         #     friend_ids.add(friendship.user_id)
#         # if friendship.friend_id != user_id:
#         #     friend_ids.add(friendship.friend_id)
#         for friendship in friendships:
#             friend_id_to_check = None
            
#             # 1. Xác định ID người bạn (ID khác user_id)
#             if friendship.user_id != user_id:
#                 friend_id_to_check = friendship.user_id
#             elif friendship.friend_id != user_id:
#                 friend_id_to_check = friendship.friend_id
            
#             if friend_id_to_check:
#                 # 2. Lấy đối tượng User từ DB (Gây nhiều DB hit)
#                 friend_user = db.session.query(User).filter_by(id=friend_id_to_check).first()
                
#                 # 3. CÚ PHÁP KIỂM TRA ĐÚNG:
#                 if friend_user and friend_user.online == True: # True tương đương với 1 trong DB
#                     friend_ids.add(friend_id_to_check)
            
#     final_ids = list(friend_ids)


#     # # Lấy thông tin User của các ID bạn bè đang online
#     # online_frs = User.query.filter(
#     #     User.id.in_(final_ids),
#     #     User.online == True
#     # ).all()

#     # online_friends = set()
#     # for fr in online_frs:
#     #     if fr.user_id != user_id:
#     #         online_friends.add(fr.user_id)
#     #     if fr.friend_id != user_id:
#     #         online_friends.add(fr.friend_id)
    
#     # realfinal_ids = list(online_friends)

#     # """
#     # Tìm tất cả ID bạn bè của người dùng hiện tại (user_id) đang online.
#     # """
#     # # 1. Lấy danh sách ID của tất cả bạn bè
#     # friend_ids_subquery = db.session.query(Friendship.from_user).filter(
#     #     Friendship.to_user == user_id
#     # ).union(
#     #     db.session.query(Friendship.to_user).filter(
#     #         Friendship.from_user == user_id
#     #     )
#     # ).subquery()
    
#     # # 2. Chỉ lọc những người bạn đang online (User.online == True)
#     # online_friend_ids = db.session.query(User.id).filter(
#     #     User.id.in_(friend_ids_subquery),
#     #     User.online == True  # <--- ĐIỀU KIỆN QUAN TRỌNG
#     # ).all()
    
#     # # Chuyển đổi kết quả sang list ID đơn giản
#     # return [id[0] for id in online_friend_ids]
#     # print(f"\n[DEBUG CORE] Tìm bạn bè cho ID {user_id}. Kết quả: {final_ids}")
    
#     return final_ids

# ---------------------------------------------------------
# SOCKET HANDLERS (Được di chuyển từ socket_events.py)
# ---------------------------------------------------------

# @socketio.on('connect')
# def handle_connect():
#     # print(f"\n[DEBUG SOCKET] FUNC CALLED: Bắt đầu xử lý CONNECT.") 
    
#     if current_user.is_authenticated:
#         user_id = current_user.id
#         # print(f"[DEBUG CONNECT] User {current_user.username} (ID: {user_id}) ĐÃ KẾT NỐI.")
#         try:
#             with db.session.no_autoflush:
#                 user = db.session.query(User).filter_by(id=user_id).first()
#                 if user:
#                     user.online = True
#                     db.session.commit()
                    
#                     room_name = f'user_{user_id}'
#                     join_room(room_name)
#                     # print(f"[DEBUG CONNECT] DB commit OK. User {user_id} đã tham gia phòng: {room_name}")
                 
#         except Exception as e:
#             # print(f"[DEBUG CONNECT] 🚨 LỖI DB trong connect: {e}")
#             traceback.print_exc()

# @socketio.on('disconnect')
# def handle_disconnect():
#     # print(f"\n[DEBUG SOCKET] FUNC CALLED: Bắt đầu xử lý DISCONNECT.")
#     if current_user.is_authenticated:
#         user_id = current_user.id
#         # username = current_user.username
#         try:
#             with db.session.no_autoflush:
#                 user = db.session.query(User).filter_by(id=current_user.id).first()
#                 if user:
#                     user.online = False
#                     db.session.commit()
#                     # print(f"[DEBUG DISCONNECT] Cập nhật User.online = False cho ID: {user.id}")

#                     # 2. Lấy danh sách bạn bè online và thông báo cho họ
#                     # Lấy danh sách các đối tượng User của bạn bè đang online
#                     online_friends = get_friends_ids(user_id)
                    
#                     # 3. GỬI LỆNH XÓA MARKER ĐẾN BẠN BÈ
#                     data_to_send = {'userId': user_id}
                    
#                     for friend_id in online_friends:
#                     #     # Gửi sự kiện 'friend:disconnected' đến room của người bạn
#                         room_name = f'user_{friend_id}'
#                         socketio.emit('friend:disconnected', data_to_send, room=room_name)
#                         print(f"[DEBUG DISCONNECT] Đã gửi lệnh xóa marker của ID {user_id} đến phòng: {room_name}")

#                     # print(f"[DEBUG DISCONNECT] Đã thông báo ngắt kết nối cho bạn bè của User ID: {user_id}")
#         except Exception as e:
#             # print(f"[DEBUG DISCONNECT] 🚨 LỖI DB trong disconnect: {e}")
#             traceback.print_exc()

# @socketio.on('update_location')
# def handle_update_location(data):
#     # print(f"\n[DEBUG SOCKET] FUNC CALLED: Bắt đầu xử lý update vị trí.") 

#     if not current_user.is_authenticated:
#         # print("[DEBUG SOCKET] WARNING: Update từ user chưa đăng nhập bị bỏ qua.")
#         return
        
#     user_id = current_user.id
    
#     try:
#         with db.session.no_autoflush:
#             # Tải lại đối tượng User an toàn
#             user = db.session.query(User).options(
#                 load_only(User.id, User.username, User.share_mode)
#             ).filter_by(id=user_id).first() 

#             if not user:
#                 # print(f"[DEBUG SOCKET] CẢNH BÁO: User ID {user_id} không tìm thấy trong DB.")
#                 return

#             # print(f"[DEBUG SOCKET] BƯỚC 1: User object tải thành công. Username: {user.username}")

#             # CẬP NHẬT LIVE LOCATION
#             location = db.session.query(LiveLocation).filter_by(user_id=user_id).first()
            
#             if location:
#                 location.lat = data.get('lat')
#                 location.lng = data.get('lng')
#             else:
#                 location = LiveLocation(user_id=user_id, lat=data.get('lat'), lng=data.get('lng'))
#                 db.session.add(location)
                
#             db.session.commit()
#             # print(f"[DEBUG SOCKET] BƯỚC 2: DB Commit LiveLocation thành công.")

#             # EMIT DỮ LIỆU
#             friend_ids = get_friends_ids(user_id)
#             share_mode_val = user.share_mode if user.share_mode else "friends" 
            
#             location_data = {
#                 "user_id": user_id,
#                 "username": user.username,
#                 "lat": data.get('lat'),
#                 "lng": data.get('lng'),
#                 "share_mode": share_mode_val
#             }
            
#             # print(f"[DEBUG SOCKET] BƯỚC 3: Chuẩn bị gửi vị trí của {user.username} đến {len(friend_ids)} người bạn. IDs: {friend_ids}")

#             for friend_id in friend_ids:
#                 room_name = f'user_{friend_id}'
                
#                 if share_mode_val == 'friends': 
#                     # print(f"[DEBUG SOCKET] Gửi vị trí đến Room: {room_name}")
#                     socketio.emit('friend_location_update', location_data, room=room_name)
#                 else:
#                     print(f"[DEBUG SOCKET] Bỏ qua gửi vị trí đến Room: {room_name} vì share_mode là {share_mode_val}")
        
#     except Exception as e:
#         # print(f"\n\n🚨🚨🚨 LỖI CRITICAL TRONG handle_update_location 🚨🚨🚨")
#         # print(f"LỖI: {e}")
#         traceback.print_exc()
#         # print(f"🚨🚨🚨 KẾT THÚC LỖI 🚨🚨🚨\n")


# ---------------------------------------------------------
# ROUTES HTTP (Được di chuyển từ routes.py)
# ---------------------------------------------------------

# Route để render trang bản đồ bạn bè
@app.route('/friends_map')
@login_required 
def friends_map_test():
    """Render file friends_map.html"""
    return render_template('friends_map.html')

# # Route API để lấy danh sách ID của bạn bè
# @app.route('/api/friends_list', methods=['GET'])
# @login_required
# def get_friends_list_api():
#     user_id = current_user.id
#     friends_ids = get_friends_ids(user_id)
#     # print(f"[DEBUG ROUTES] API /api/friends_list trả về ID: {friends_ids}")
#     return jsonify({"friends_ids": friends_ids}), 200

# # Route API để JavaScript lấy thông tin người dùng (Đã có trong app.py)
# @app.route('/api/current_user_info')
# @login_required 
# def get_current_user_info():
#     """Cung cấp user_id và username cho JavaScript."""
#     return jsonify({
#         'user_id': current_user.id,
#         'username': current_user.username,
#         'share_mode': current_user.share_mode 
#     })

# # Trong app.py (Thêm vào cùng vị trí với các API khác)
# @app.route('/api/share_mode', methods=['POST'])
# @login_required
# def update_share_mode():
#     data = request.get_json()
#     mode = data.get('mode')
#     user_id = current_user.id
    
#     if mode in ['friends', 'hidden']:
#         current_user.share_mode = mode
#         db.session.commit()
        
#         # Nếu chuyển sang HIDDEN, phải gửi event xóa marker cho tất cả bạn bè
#         # if mode == 'hidden':
#         #     # Hàm get_friends_ids đã được định nghĩa trong app.py
#         #     friend_ids = get_friends_ids(user_id) 
#         #     for friend_id in friend_ids:
#         #         # Gửi event để client tự xóa marker của người này
#         #         socketio.emit('friend:disconnected', {'userId': user_id}, room=f'user_{friend_id}')
        
#         return jsonify({"message": "Share mode updated", "new_mode": mode}), 200
#     return jsonify({"message": "Invalid mode"}), 400

# # Trong app.py
# @app.route('/api/initial_locations', methods=['GET'])
# @login_required
# def initial_locations():
#     user_id = current_user.id
    
#     # Lấy ID của tất cả bạn bè (đang share_mode='friends' hoặc chưa set)
#     friend_ids = get_friends_ids(user_id) # Hàm đã có của bạn
    
#     # 1. Lấy LiveLocation của tất cả bạn bè đã tìm được
#     # Cần phải JOIN với bảng User để lấy username và share_mode
#     locations = db.session.query(LiveLocation, User.username, User.share_mode).join(User, LiveLocation.user_id == User.id).filter(
#         LiveLocation.user_id.in_(friend_ids)
#     ).all()
    
#     result = []
#     for loc, uname, mode in locations:
#         # Chỉ hiển thị vị trí cuối nếu họ không ở chế độ 'hidden'
#         #if mode != 'hidden':
#         result.append({
#             'user_id': loc.user_id,
#             'username': uname,
#             'lat': loc.lat,
#             'lng': loc.lng,
#             'share_mode': mode
#         })
            
#     # Thêm vị trí của chính mình (để đảm bảo map bao trùm cả mình)
#     my_location = db.session.query(LiveLocation).filter_by(user_id=user_id).first()
#     if my_location:
#          result.append({
#             'user_id': user_id,
#             'username': current_user.username,
#             'lat': my_location.lat,
#             'lng': my_location.lng,
#             'is_self': True
#         })

#     return jsonify({"locations": result}), 200



# =========================================================
# 5. KHỞI CHẠY SERVER
# =========================================================
if __name__ == "__main__":
    print("=== System Starting ===")

    # Tạo context để đảm bảo truy cập được DB
    with app.app_context():
        # db.create_all()  # Uncomment nếu bạn muốn tạo bảng mới (cẩn thận mất dữ liệu cũ)
        pass
    
    print(print(app.config["SQLALCHEMY_DATABASE_URI"]))
    print(f"🚀 Server đang chạy tại: http://localhost:5000")
    print(f"🗺️  MapRouting module tại: http://localhost:5000/MapRouting/")

    # app.run(debug=True, use_reloader=False)
    # socketio.run(app, debug=False, use_reloader=False)
    socketio.run(app, host="0.0.0.0", port=5001, debug=False, use_reloader=False)