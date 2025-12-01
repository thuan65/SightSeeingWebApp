from flask import Blueprint, request, jsonify 
from flask_login import current_user 
from models import db, ConversationHistory 
from .chatBotLogic import chatbot_reply

# ---------------------------------------------------------
# CHATBOT
# ---------------------------------------------------------

chatBot_bp = Blueprint("chat_bot", __name__)

@chatBot_bp.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    if not data or "message" not in data:
        return jsonify({"error": "Missing 'message' in request"}), 400

    user_message = data["message"].strip()
    if not user_message:
        return jsonify({"error": "Empty message"}), 400

    try:
        bot_response = chatbot_reply(user_message)
        #Kiểm tra nếu người dùng đã đăng nhập thì lưu vào DB
        if current_user.is_authenticated:
            new_history = ConversationHistory(
                session_type='chatbot',
                user_id=current_user.id,
                user_message=user_message,
                system_response=bot_response
            )
            db.session.add(new_history)
            db.session.commit()
            print(f"Đã lưu lịch sử chat cho user {current_user.username}")
            # DEBUG
        else:
            print("DEBUG: User đang là 'Anonymous' (Vô danh) -> KHÔNG LƯU DB")
            #Trả kết quả 
        return jsonify({
            "reply": bot_response,
            "saved": current_user.is_authenticated # Báo hiệu đã lưu hay chưa
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# ---------------------------------------------------------
# API LẤY LỊCH SỬ CHAT CŨ (Load khi mở trang chat)
# ---------------------------------------------------------
@chatBot_bp.route("/api/history", methods=["GET"])
def get_chat_history():
    # Chỉ lấy lịch sử nếu đã đăng nhập
    if not current_user.is_authenticated:
        return jsonify([]) # Trả về mảng rỗng nếu chưa login

    try:
        # Lấy tin nhắn của user hiện tại, sắp xếp cũ nhất -> mới nhất
        histories = ConversationHistory.query.filter_by(user_id=current_user.id)\
            .order_by(ConversationHistory.timestamp.asc()).all()
        
        return jsonify([h.to_dict() for h in histories])
    except Exception as e:
        return jsonify({"error": str(e)}), 500