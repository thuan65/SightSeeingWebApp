# LocationSharing/socket_events.py

from flask_socketio import emit, join_room, leave_room
from flask_login import current_user
from extensions import db
from models import LiveLocation, User
from .routes import get_friends_ids
from datetime import datetime
from sqlalchemy.orm import load_only
import traceback
import math

def register_events(socketio):

    @socketio.on('connect')
    def handle_connect():
        # print(f"\n[DEBUG SOCKET] FUNC CALLED: Bắt đầu xử lý CONNECT.") 
        
        if current_user.is_authenticated:
            user_id = current_user.id
            # print(f"[DEBUG CONNECT] User {current_user.username} (ID: {user_id}) ĐÃ KẾT NỐI.")
            try:
                with db.session.no_autoflush:
                    user = db.session.query(User).filter_by(id=user_id).first()
                    if user:
                        user.online = True
                        db.session.commit()
                        
                        room_name = f'user_{user_id}'
                        join_room(room_name)
                        # print(f"[DEBUG CONNECT] DB commit OK. User {user_id} đã tham gia phòng: {room_name}")
                    
            except Exception as e:
                # print(f"[DEBUG CONNECT] 🚨 LỖI DB trong connect: {e}")
                traceback.print_exc()


    @socketio.on('disconnect')
    def handle_disconnect():
        # print(f"\n[DEBUG SOCKET] FUNC CALLED: Bắt đầu xử lý DISCONNECT.")
        if current_user.is_authenticated:
            user_id = current_user.id
            # username = current_user.username
            try:
                with db.session.no_autoflush:
                    user = db.session.query(User).filter_by(id=current_user.id).first()
                    if user:
                        user.online = False
                        db.session.commit()
                        # print(f"[DEBUG DISCONNECT] Cập nhật User.online = False cho ID: {user.id}")

                        # 2. Lấy danh sách bạn bè online và thông báo cho họ
                        # Lấy danh sách các đối tượng User của bạn bè đang online
                        online_friends = get_friends_ids(user_id)
                        
                        # 3. GỬI LỆNH XÓA MARKER ĐẾN BẠN BÈ
                        data_to_send = {'userId': user_id}
                        
                        for friend_id in online_friends:
                        #     # Gửi sự kiện 'friend:disconnected' đến room của người bạn
                            room_name = f'user_{friend_id}'
                            socketio.emit('friend:disconnected', data_to_send, room=room_name)
                            print(f"[DEBUG DISCONNECT] Đã gửi lệnh xóa marker của ID {user_id} đến phòng: {room_name}")

                        # print(f"[DEBUG DISCONNECT] Đã thông báo ngắt kết nối cho bạn bè của User ID: {user_id}")
            except Exception as e:
                # print(f"[DEBUG DISCONNECT] 🚨 LỖI DB trong disconnect: {e}")
                traceback.print_exc()


    @socketio.on('update_location')
    def handle_update_location(data):
        # print(f"\n[DEBUG SOCKET] FUNC CALLED: Bắt đầu xử lý update vị trí.") 

        if not current_user.is_authenticated:
            # print("[DEBUG SOCKET] WARNING: Update từ user chưa đăng nhập bị bỏ qua.")
            return
            
        user_id = current_user.id
        
        try:
            with db.session.no_autoflush:
                # Tải lại đối tượng User an toàn
                user = db.session.query(User).options(
                    load_only(User.id, User.username, User.share_mode)
                ).filter_by(id=user_id).first() 

                if not user:
                    # print(f"[DEBUG SOCKET] CẢNH BÁO: User ID {user_id} không tìm thấy trong DB.")
                    return

                # print(f"[DEBUG SOCKET] BƯỚC 1: User object tải thành công. Username: {user.username}")

                # CẬP NHẬT LIVE LOCATION
                location = db.session.query(LiveLocation).filter_by(user_id=user_id).first()
                
                if location:
                    location.lat = data.get('lat')
                    location.lng = data.get('lng')
                else:
                    location = LiveLocation(user_id=user_id, lat=data.get('lat'), lng=data.get('lng'))
                    db.session.add(location)
                    
                db.session.commit()
                # print(f"[DEBUG SOCKET] BƯỚC 2: DB Commit LiveLocation thành công.")

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
                
                # print(f"[DEBUG SOCKET] BƯỚC 3: Chuẩn bị gửi vị trí của {user.username} đến {len(friend_ids)} người bạn. IDs: {friend_ids}")

                for friend_id in friend_ids:
                    room_name = f'user_{friend_id}'
                    
                    if share_mode_val == 'friends': 
                        # print(f"[DEBUG SOCKET] Gửi vị trí đến Room: {room_name}")
                        socketio.emit('friend_location_update', location_data, room=room_name)
                    else:
                        print(f"[DEBUG SOCKET] Bỏ qua gửi vị trí đến Room: {room_name} vì share_mode là {share_mode_val}")
            
        except Exception as e:
            # print(f"\n\n🚨🚨🚨 LỖI CRITICAL TRONG handle_update_location 🚨🚨🚨")
            # print(f"LỖI: {e}")
            traceback.print_exc()
            # print(f"🚨🚨🚨 KẾT THÚC LỖI 🚨🚨🚨\n")
