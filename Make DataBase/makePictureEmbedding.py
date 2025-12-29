
from models_loader import Clip_model, processor, model
import faiss
from PIL import Image as PILImage
import torch, os, json
import numpy as np
from models import Image, FaissMapping
from extensions import db
from __init__ import create_app

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
tmp_DIR = os.path.join(BASE_DIR, "static")

file_path_PicturevectorDatabase = os.path.join(tmp_DIR, "images")

def get_image_embedding(image_path):
    image = PILImage.open(image_path).convert("RGB")
    inputs = processor(images=image, return_tensors="pt")
    with torch.no_grad():
        emb = model.get_image_features(**inputs)
    return emb / emb.norm(dim=-1, keepdim=True)

def is_url(path):
    return path.startswith("http://") or path.startswith("https://")


def generate_Picture_embeddings_to_db():
    app = create_app()
    with app.app_context():
        # Clear old mapping
        FaissMapping.query.delete()
        db.session.commit()

        images = db.session.query(Image.id, Image.filename).all()
       
        metadata = {}
        embeddings = []

        for idx, (image_id, filename) in enumerate(images):
            if (is_url(filename) or not filename):
                continue; # skip url

            file_path = os.path.join(file_path_PicturevectorDatabase, filename)
            try:
                vector_data = get_image_embedding(file_path).cpu().numpy().astype("float32")
                embeddings.append(vector_data) #list cá data
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
            print("Embedding picture id: ", image_id)
            metadata[len(embeddings) - 1] = {
                "image_id": image_id,
                "place_id": len(embeddings) - 1,# Vị trí ảnh trong vector database
                "filename": filename
            }


    with open("instance/metadata.json", "w", encoding= "utf-8") as f:
        json.dump(metadata, f, indent=2)

    embeddings = np.vstack(embeddings)  # Chuyển list (1,D) → array (N,D)
    return embeddings

def build_faiss_index(file_path="PlacePictureDescription.index"):
    embeddings = generate_Picture_embeddings_to_db()
    faiss.normalize_L2(embeddings)
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)
    faiss.write_index(index, file_path)
    print(f"FAISS index created: {file_path}, total vectors: {index.ntotal}")

if __name__ == "__main__":
    build_faiss_index()
