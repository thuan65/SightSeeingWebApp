# Messaging/socket_events.py

from flask_socketio import emit, join_room
from flask_login import current_user
from extensions import db
from models import Message, User 

# Hàm đăng ký các events, được gọi từ __init__.py
def register_events(socketio):
    
    # Hàm hỗ trợ: Định danh phòng chat giữa hai người
    def get_chat_room(user1_id, user2_id):
        # Tạo tên phòng dựa trên ID nhỏ hơn và ID lớn hơn để đảm bảo tính duy nhất
        ids = sorted([user1_id, user2_id])
        return f"chat_{ids[0]}_{ids[1]}"


    # =========================================================================
    # 1. EVENT: JOIN_CHAT (Tham gia phòng chat cụ thể)
    # =========================================================================
    @socketio.on('join_chat')
    def handle_join_chat(data):
        if not current_user.is_authenticated:
            return 
        
        target_id = data.get('target_id')
        if not target_id:
            return

        room = get_chat_room(current_user.id, target_id)
        join_room(room)
        
        # Gửi thông báo đến chính mình
        emit('status_message', {'msg': f"Đã tham gia phòng chat với User {target_id}.", 'room': room}, room=room)
        
        print(f"[DEBUG CHAT] User {current_user.id} joined room: {room}")


    # =========================================================================
    # 2. EVENT: SEND_MESSAGE (Gửi tin nhắn)
    # =========================================================================
    @socketio.on('send_message')
    def handle_send_message(data):
        if not current_user.is_authenticated:
            return 
            
        receiver_id = data.get('receiver_id')
        content = data.get('content')
        
        if not receiver_id or not content:
            return
            
        try:
            # 1. Lưu tin nhắn vào DB
            new_message = Message(
                sender_id=current_user.id,
                receiver_id=receiver_id,
                content=content
            )
            db.session.add(new_message)
            db.session.commit()

            # 2. Xây dựng payload để gửi qua Socket
            room = get_chat_room(current_user.id, receiver_id)
            
            message_payload = {
                'id': new_message.id,
                'sender_id': current_user.id,
                'content': content,
                'timestamp': new_message.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            }

            # 3. Phát sóng tin nhắn đến tất cả người dùng trong phòng chat
            emit('new_message', message_payload, room=room)
            
            print(f"[DEBUG CHAT] Gửi tin nhắn từ {current_user.id} đến {receiver_id} trong phòng {room}")

        except Exception as e:
            print(f"[DEBUG CHAT] 🚨 LỖI khi lưu tin nhắn: {e}")
            db.session.rollback()