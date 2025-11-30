from flask import Blueprint
import json
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
        return jsonify({"reply": bot_response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500