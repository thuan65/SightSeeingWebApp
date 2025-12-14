# Messaging/routes.py

from . import messaging_bp # Import Blueprint từ file khởi tạo chính ngoài
from flask import jsonify, request
from flask_login import current_user, login_required
from sqlalchemy import or_
from extensions import db
from models import Message, User 
from datetime import datetime


# =========================================================================
# API: Lấy Lịch sử Tin nhắn giữa User hiện tại và Target User
# Route: /messaging/api/history/<int:target_user_id>
# =========================================================================
@messaging_bp.route("/api/history/<int:target_user_id>", methods=["GET"])
@login_required
def get_message_history(target_user_id):
    current_user_id = current_user.id
    
    # Lấy tin nhắn giữa hai người (gửi hoặc nhận)
    messages = db.session.query(Message).filter(
        or_(
            (Message.sender_id == current_user_id) & (Message.receiver_id == target_user_id),
            (Message.sender_id == target_user_id) & (Message.receiver_id == current_user_id)
        )
    ).order_by(Message.timestamp.asc()).all() # Lấy tất cả tin nhắn
    
    history = []
    for msg in messages:
        history.append({
            'id': msg.id,
            'sender_id': msg.sender_id,
            'content': msg.content,
            'timestamp': msg.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'is_self': msg.sender_id == current_user_id
        })
        
    return jsonify({"messages": history}), 200