from transformers import CLIPProcessor, CLIPModel
from models_loader import Clip_model, processor, model
from PIL import Image
import torch, os, json

# === Load metadata (địa điểm) ===
with open("metadata.json", "r", encoding="utf-8") as f:
    metadata = json.load(f)




def find_similar(image_query_path):
    query_emb = get_image_embedding(image_query_path)
    similarities = (query_emb @ db_embeddings.T).squeeze(0)
    best_idx = similarities.argmax().item()
    return db_names[best_idx], similarities[best_idx].item()

def main():

    best_match, score = find_similar("static/ThuNghiem.jpg")
    print(best_match, score)
    pass


if __name__ == "__main__":
    main()