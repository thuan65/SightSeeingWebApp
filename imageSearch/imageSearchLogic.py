from transformers import CLIPProcessor, CLIPModel
from models_loader import Clip_model, processor, model
from PIL import Image
import torch, os, json

# === Load metadata (địa điểm) ===
with open("metadata.json", "r", encoding="utf-8") as f:
    metadata = json.load(f)

# === Load database images ===
db_dir = "static/images" # nơi chứa ảnh gốc để so sánh 
db_embeddings = []
db_names = []

def get_image_embedding(image_path):
    image = Image.open(image_path).convert("RGB")
    inputs = processor(images=image, return_tensors="pt")
    with torch.no_grad():
        emb = model.get_image_features(**inputs)
    return emb / emb.norm(dim=-1, keepdim=True)

print("Embedding")
for fname in os.listdir(db_dir):
    path = os.path.join(db_dir, fname)
    emb = get_image_embedding(path)
    db_embeddings.append(emb)
    db_names.append(fname)
db_embeddings = torch.cat(db_embeddings, dim=0)

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