from sentence_transformers import util
from models_loader import sbert_model
import google.generativeai as genai
import torch
import os
from dotenv import load_dotenv
from sentence_transformers.util import cos_sim

from flask import Flask, current_app, copy_current_request_context, has_app_context, has_request_context
from models import ConversationHistory, Image, FaissMapping
import faiss_loader
from extensions import db

import faiss
import numpy as np


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(BASE_DIR, "system_prompt.txt")


with open(file_path, 'r', encoding='utf-8') as file:
    SYSTEM_PROMPT = file.read()


# ======================================================
#Load môi trường & cấu hình API key
# ======================================================
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# ======================================================
#Khởi tạo model
# ======================================================
# Mô hình hiểu ngữ nghĩa cho tiếng Việt
# sem_model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

# Mô hình hội thoại Gemini
gemini_model = genai.GenerativeModel("gemini-2.5-flash")
# gemini_model = genai.GenerativeModel("gemini-live-2.5-flash")

def aTemporaryCreateApp():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///FlaskDataBase.db"
    db.init_app(app)
    return app

# ======================================================
# Phân loại ý định người dùng
# ======================================================
def detect_intent(text: str) -> str:
    """
    Phân loại ý định người dùng:
    - suggest: muốn gợi ý địa điểm
    - info: hỏi thông tin cụ thể
    - chat: trò chuyện tự nhiên
    """
    text_lower = text.lower()
    keywords = ["đi", "du lịch", "địa điểm", "ở đâu", "biển", "núi", "tham quan", "đến"]

    if any(k in text_lower for k in keywords):
        return "suggest"
    elif "ở" in text_lower and "gì" in text_lower:
        return "info"
    else:
        return "chat"

# ======================================================
#Gợi ý địa điểm từ cơ sở dữ liệu
# ======================================================

def suggest_place(user_query: str, top_k: int = 3) -> dict:
    # Encode query
    query_emb = sbert_model.encode([user_query], convert_to_numpy=True)
    query_emb = query_emb.astype('float32')
    faiss.normalize_L2(query_emb)  # nếu index đã normalize

    distances, indices = faiss_loader.faiss_Text_index.search(query_emb, top_k)

    results = []

    app = aTemporaryCreateApp()

    with app.app_context():
        for idx in indices[0]:  # indices[0] là mảng các index của top_k
            image_id = faiss_loader.index_to_image_id[idx]
            image = Image.query.get(image_id)
            if image:  # an toàn nếu record tồn tại
                results.append({
                    "id": image.id,
                    "name": image.name,
                    "tag": image.tags,
                    "address": image.address,
                    "description": image.description
                })

    return results


# ======================================================
#Kiểm tra câu hỏi có nằm trong phạm vi sightseeing
# ======================================================
def is_sightseeing_question(user_message: str) -> bool:
    keywords = [
        "đi đâu", "chơi gì", "du lịch", "tham quan", "địa điểm",
        "quán", "chỗ nào", "review", "gần đây có gì",
        "đi chơi", "khám phá", "landmark", "điểm đến"
    ]
    msg = user_message.lower()
    return any(k in msg for k in keywords)

# ======================================================
# Truy vấn database để lấy lịch sử chat
# ======================================================

def load_chat_history(user_id: str):
    # Lấy tất cả message của user, sắp xếp theo thời gian
    logs = ConversationHistory.query.filter_by(user_id=user_id).order_by(ConversationHistory.timestamp).all()
    
    # Tạo list message theo format OpenAI / Gemini
    chat_history = []
    for log in logs:
        chat_history.append({
            "role": log.role,
            "content": log.content
        })
    return chat_history

# ======================================================
# Trả lời bằng Gemini
# ======================================================

def gemini_reply(user_message: str) -> str:
    """
    Gửi user_message đến Gemini và trả về phản hồi dạng chuỗi.
    """
    try:
        response = gemini_model.generate_content(user_message, stream= True)
        return response.text
    except Exception as e:
        return f"Lỗi khi gọi Gemini API: {e}"
    
def gemini_stream(user_message: str):
 
    try:
        response = gemini_model.generate_content(
            user_message, 
            stream=True
        )
        for chunk in response:
            if chunk.text:
                yield f"data: {chunk.text}\n\n"
    except Exception as e:
        yield f"data: Lỗi khi gọi Gemini API: {e}\n\n"



# ======================================================
# 7. Hàm trung tâm: Chatbot trả lời
# ======================================================
# def chatbot_reply(user_message: str):
# # Sinh phản hồi dựa trên intent.
#     intent = detect_intent(user_message)

#     if intent == "suggest":
#         place = suggest_place(user_message)
#         raw_info = f" Gợi ý cho bạn: {place['name']} — {place['description']}"
#         prompt = f"""Người dùng hỏi: "{user_message}".
#         Dưới đây là thông tin tôi tìm thấy:
#         {raw_info}
#         Hãy viết lại câu trả lời ngắn gọn, thân thiện, tự nhiên như hướng dẫn viên du lịch đang nói chuyện, bằng tiếng Việt.
#         """
#         reply = gemini_reply(prompt)
#     else:
#         reply = gemini_reply(user_message)

#     return reply



def chatbot_reply(user_message: str):
    intent = detect_intent(user_message)

   

    if intent == "suggest":
        places = suggest_place(user_message)
        raw_info = "\n".join([f"{p['name']} — {p['description']}" for p in places])

        prompt = f"""
        # SYSTEM INSTRUCTION
        {SYSTEM_PROMPT}

        # USER MESSAGE
        Người dùng hỏi: "{user_message}"

        # ASSISTANT RESOURCES
        Dưới đây là thông tin tôi tìm thấy từ cơ sở dữ liệu nội bộ:
        {raw_info}

        # TASK
        Dựa trên SYSTEM_INSTRUCTION + USER_MESSAGE + ASSISTANT_RESOURCES,
        hãy viết câu trả lời ngắn gọn, thân thiện, tự nhiên như hướng dẫn viên du lịch đang nói chuyện, bằng tiếng Việt.
        """

        reply = gemini_stream(prompt)

    else:
        # Trường hợp không suggest thì chỉ gộp SYSTEM_PROMPT + user input
        prompt = f"""
        # SYSTEM INSTRUCTION
        {SYSTEM_PROMPT}

        # USER MESSAGE
        {user_message}

        # TASK
        Dựa trên SYSTEM_INSTRUCTION + USER_MESSAGE, hãy trả lời tự nhiên và đúng yêu cầu.
        """
    reply = gemini_stream(prompt)

    return reply

print("Chat Bot loaded")
