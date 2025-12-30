from sentence_transformers import util
from models_loader import sbert_model
import google.generativeai as genai
import torch
import os, json
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

# Mô hình hội thoại Gemini
gemini_model = genai.GenerativeModel("gemini-2.5-flash")

def aTemporaryCreateApp():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///FlaskDataBase.db"
    db.init_app(app)
    return app                                                              
# ======================================================

# ===================  Intent dectector =================== 
INTENT_KEYWORDS = {
    "suggest": [
          "gợi ý", "đề xuất", "nên đi", "muốn đi",
    "đi đâu", "chỗ nào", "ở đâu chơi",
    "gần đây", "địa điểm", "tham quan",
    "nơi vui chơi", "điểm đến", "tham quan đâu",
    "tour", "chuyến đi", "lịch trình",
    "du lịch", "check-in", "khám phá",
    "địa điểm nổi tiếng", "địa điểm đẹp"
    ],
    "info": [
        "ở đâu", "là gì", "giá vé",
        "mở cửa", "địa chỉ",
        "giờ mở cửa", "bao nhiêu tiền",
        "giới thiệu", "thông tin"
    ],
    "chat": [
        "hello", "hi", "chào",
        "bạn là ai", "giúp gì",
        "nói chuyện", "cảm ơn"
    ]
}

INTENT_PRIORITY = ["suggest", "info", "chat"]

# ======================================================
# Phân loại ý định người dùng
# ======================================================
def detect_intent(text: str) -> str:
    text = text.lower()

    scores = {intent: 0 for intent in INTENT_PRIORITY}

    for intent, keywords in INTENT_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                scores[intent] += 1
    # Thứ tự ưu tiên là suggest -> info -> chat
    for intent in INTENT_PRIORITY:
        if scores[intent] > 0:
            return intent

    return "chat"
# =================== Intent dectector =================== 

# ======================================================
#Gợi ý địa điểm từ cơ sở dữ liệu
# ======================================================

# ======================================================
# COSINE SIMILARITY HELPER
# Trả về danh sách địa điểm giống trên một tiêu chí nhất định
def threshold_search(query_emb):
    top_k = 50
    threshold = 0.38
    distances, indices = faiss_loader.faiss_Text_index.search(query_emb, top_k)
    results = [
        {"id": idx, "score": score}
        for idx, score in zip(indices[0], distances[0])
        if score >= threshold
]
    return results
# ======================================================

def query_places(user_query: str) -> dict:
  
    # Encode query
    query_emb = sbert_model.encode([user_query], convert_to_numpy=True)
    query_emb = query_emb.astype('float32')
    faiss.normalize_L2(query_emb)  # nếu index đã normalize
    topK_Similarity_List = threshold_search(query_emb)

# DEBUG AREA
    # print("############################")
    # for r in topK_Similarity_List:
    #     print(r["id"], r["score"])
# DEBUG AREA

    results = [] 

    app = aTemporaryCreateApp()

    with app.app_context():
        for idx in [item["id"] for item in topK_Similarity_List]:
            image_id = faiss_loader.index_to_image_id[idx]
            image = Image.query.get(image_id)
            if image:  # an toàn nếu record tồn tại
                results.append({
                    **image.to_dict()
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
    
    # Tạo list message theo format Gemini
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

# === Trả lời khi có đủ kết quả ===
def gemini_reply(user_message: str) -> str:
    try:
        response = gemini_model.generate_content(user_message)
        return response.text
    except Exception as e:
        return f"Lỗi khi gọi Gemini API: {e}"
# === Trả lời khi có đủ kết quả ===    

# === Trả lời từ ký tự ===
def gemini_stream(user_message: str):
 
        response = gemini_model.generate_content(
            user_message, 
            stream=True
        )
        for chunk in response:
            if chunk.text:
                yield chunk.text
# === Trả lời từ ký tự ===

# =================== Enity dealing =================== 
def extract_entities(user_message):
    prompt = f"""
    Trích xuất entity từ câu sau dưới dạng JSON.
    CÁC TRƯỜNG:
    - place_name (string | null)
    - place_type (string | null)
    - location (string | null)
    - attribute (string | null)

    Câu: "{user_message}"
    """

    result = gemini_reply(prompt)
    return json.loads(result)
# =================== Tách Enity =================== 
# =================== Enity dealing =================== 

# =================== Context dealing =================== 
def resolve_entities(entities, context):
    if entities["place_name"] is None:
        entities["place_name"] = context.get("last_place")

    return entities


def update_context(context, intent, entities, places):
    context["last_intent"] = intent

    if entities.get("place_name"):
        context["last_place"] = entities["place_name"]

    if places:
        context["last_places"] = places[:3]  # lưu vài chỗ gần nhất

# =================== Context dealing =================== 

# ===================BUILD PROMPT======================
def build_suggest_Prompt(user_message: str, places):
    raw_info = "\n".join([f"{p['name']} — {p['tags']}" for p in places])
    return raw_info

def build_info_Prompt(user_messgae: str, places):
    raw_info = "\n".join([f"{p['name']} — {p['description']}" for p in places])#add rating, address nếu thấy cần thiết về sau
    return raw_info

def build_safe_prompt(intent, data):
    raw_info = "intent: chat - Chỉ trò chuyện thân thiện, không đề cập địa điểm mới."
    return raw_info


# ======================================================
# 7. Chat Bot trả lời
# ======================================================
def chatbot_reply(user_message: str,  places, intent):

    try:
        if intent == "suggest":
            raw_info = build_suggest_Prompt(user_message, places)

            prompt = f"""
            Hãy trả lời thật ngắn các thông tin của các địa điểm.
            # SYSTEM INSTRUCTION
            {SYSTEM_PROMPT}

            # USER MESSAGE
            Người dùng hỏi: "{user_message}"

            # ASSISTANT RESOURCES
            Dưới đây là thông tin tôi tìm thấy từ cơ sở dữ liệu nội bộ:
            {raw_info}

            """
        elif intent == "info":
            raw_info = build_info_Prompt(user_message, places)
            
            prompt = f"""
            # SYSTEM INSTRUCTION
            {SYSTEM_PROMPT}

            # USER MESSAGE
            {user_message}

            # ASSISTANT RESOURCES
            Dưới đây là thông tin tôi tìm thấy từ cơ sở dữ liệu nội bộ:
            {raw_info}

            """
        else: # chat
            raw_info = build_info_Prompt(user_message, places)
            
            prompt = f"""
            # SYSTEM INSTRUCTION
            {SYSTEM_PROMPT}

            # USER MESSAGE
            {user_message}

            # ASSISTANT RESOURCES
            {raw_info}

            """

        
        for chunk in gemini_stream(prompt):
            yield chunk

    except Exception as e:
         # Nếu Gemini API lỗi, hết quota...
        print(f"Gemini API lỗi: {e}. Chuyển sang rule-based.")
        fallback_reply = rule_based_reply(user_message, places, intent)

        for line in fallback_reply.split("\n"):
            yield line

# ===================BUILD PROMPT======================

# Một phiên bản rule-based fallback nếu Gemini API không dùng được.
def rule_based_reply(user_message: str, places, intent):
    
    if intent == "suggest" and places:
        # trả lời dựa trên cơ sở dữ liệu
        return "\n".join([f"{p['name']} — {p['description']}" for p in places])  # lấy tối đa 5 địa điểm
    elif intent == "info":
        return "\n".join([f"{p['name']}: {p['description']}" for p in places])
    else:
        # fallback generic
        return f"Xin lỗi, tôi chưa hiểu ý của bạn."