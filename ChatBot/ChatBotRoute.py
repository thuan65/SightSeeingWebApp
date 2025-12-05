from flask import Blueprint, request, jsonify, Response, current_app
from flask_login import current_user 
from models import db, ConversationHistory 
from .chatBotLogic import chatbot_reply

# ---------------------------------------------------------
# CHATBOT
# ---------------------------------------------------------

chatBot_bp = Blueprint("chat_bot", __name__)

# @chatBot_bp.route("/stream", methods=["POST"])
# def stream():
#     data = request.get_json()
#     user_message = data.get("message", "")
#     print("Client gửi:", user_message)

#     def generate():
#         for chunk in chatbot_reply(user_message):
#             yield chunk   # Đã bao gồm "data: ...\n\n"

#         yield "data: [DONE]\n\n"

#     return Response(generate(), mimetype="text/event-stream")

@chatBot_bp.route("/stream", methods=["POST"])
def stream():
    data = request.get_json()
    if not data or "message" not in data:
        return jsonify({"error": "Missing 'message' in request"}), 400

    user_message = data.get("message", "").strip()
    if not user_message:
        return jsonify({"error": "Empty message"}), 400

    # Lưu thông tin user trước khi generate() làm mất context
    user_is_auth = current_user.is_authenticated
    user_id = current_user.id if user_is_auth else None

    full_bot_reply = []
    real_app = current_app._get_current_object()
    try:
        def generate():

            for chunk in chatbot_reply(user_message):
                clean = chunk.replace("data: ", "").strip()
                full_bot_reply.append(clean)
                yield chunk

            # Ghép bot trả lời
            bot_response = "".join(full_bot_reply)

            # LƯU DB
            if user_is_auth:
                with real_app.app_context():
                    new_history = ConversationHistory(
                        session_type='chatbot',
                        user_id=user_id,
                        user_message=user_message,
                        system_response=bot_response
                    )
                    db.session.add(new_history)
                    db.session.commit()
                    print(f"Đã lưu lịch sử chat user_id={user_id}")

            else:
                print("User Anonymous → Không lưu")

            # Thông báo kết thúc stream
            yield "data: [DONE]\n\n"

        return Response(generate(), mimetype="text/event-stream")

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


  #Trả kết quả 
        # return jsonify({
        #     "reply": bot_response,
        #     "saved": current_user.is_authenticated # Báo hiệu đã lưu hay chưa
        # })

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
    

