from sentence_transformers import SentenceTransformer, util
from sqlalchemy import create_engine, text
import google.generativeai as genai
import torch
import os
from dotenv import load_dotenv

# ======================================================
# 1. Load môi trường & cấu hình API key
# ======================================================
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# ======================================================
# 2️. Khởi tạo model
# ======================================================
# Mô hình hiểu ngữ nghĩa cho tiếng Việt
sem_model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

# Mô hình hội thoại Gemini
gemini_model = genai.GenerativeModel("gemini-2.5-flash")

# ======================================================
# 3️. Kết nối database
# ======================================================
engine = create_engine("sqlite:///places.db")

with engine.connect() as conn:
    results = conn.execute(text("SELECT * FROM places")).mappings().all()

# Chuẩn bị embedding cho toàn bộ địa điểm
place_sentences = [f"{r['name']} - {r['description']}" for r in results]
place_embeddings = sem_model.encode(place_sentences, convert_to_tensor=True)

# ======================================================
# 4️. Phân loại ý định người dùng
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
# 5️. Gợi ý địa điểm từ cơ sở dữ liệu
# ======================================================
def suggest_place(user_query: str) -> dict:
    """
    Trả về địa điểm có mô tả gần nhất với truy vấn người dùng.
    """
    query_embedding = sem_model.encode(user_query, convert_to_tensor=True)
    scores = util.cos_sim(query_embedding, place_embeddings)[0]
    best_idx = scores.argmax().item()
    return dict(results[best_idx])

# ======================================================
# 6️. Trả lời bằng Gemini
# ======================================================
def gemini_reply(user_message: str) -> str:
    """
    Sinh phản hồi bằng Gemini.
    """
    chat = gemini_model.start_chat()
    response = chat.send_message(user_message)
    return response.text.strip()

# ======================================================
# 7️. Hàm trung tâm: Chatbot trả lời
# ======================================================
def chatbot_reply(user_message: str):
    """
    Sinh phản hồi dựa trên intent.
    """
    intent = detect_intent(user_message)

    if intent == "suggest":
        place = suggest_place(user_message)
        reply = f"💡 Gợi ý cho bạn: {place['name']} — {place['description']}"
    else:
        reply = gemini_reply(user_message)

    return reply

print(chatbot_reply("Hello"))
