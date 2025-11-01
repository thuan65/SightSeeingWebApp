from sentence_transformers import SentenceTransformer, util
from sqlalchemy import create_engine, text
import json

# Load model
model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')

# Kết nối tới database SQLite
engine = create_engine("sqlite:///places.db")
# Load data
with engine.connect() as conn:
    results = conn.execute(text("SELECT * FROM places")).mappings().all()

place_sentences = [f"{r['name']} - {r['description']}" for r in results]
place_embeddings = model.encode(place_sentences, convert_to_tensor=True)

def suggest_place(user_query):
    query_embedding = model.encode(user_query, convert_to_tensor=True)
    scores = util.cos_sim(query_embedding, place_embeddings)[0]
    best_idx = scores.argmax().item()
    best_score = scores[best_idx].item()
    return results[best_idx], best_score

# Ví dụ chạy thử
query = input()
result, score = suggest_place(query)
print(f"Gợi ý: {result['name']} ({result['city']}) - độ phù hợp: {score:.2f}")
