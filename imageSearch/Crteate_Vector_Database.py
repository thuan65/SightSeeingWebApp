from transformers import CLIPProcessor, CLIPModel

import torch, os, json, sys
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR) #Ra 1 cấp thư mục
# Thêm thư mục cha vào sys.path
sys.path.append(PARENT_DIR)

from models_loader import Clip_model, processor, model
from PIL import Image

import faiss

# === Embedding tất cả ảnh ===#
def get_image_embedding(image_path):
    image = Image.open(image_path).convert("RGB")
    inputs = processor(images=image, return_tensors="pt")
    with torch.no_grad():
        emb = model.get_image_features(**inputs)
    return emb / emb.norm(dim=-1, keepdim=True)


def main():

    # === Load database images ===
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    PARENT_DIR = os.path.dirname(BASE_DIR) #Ra 1 cấp thư mục
    tmp_dir = os.path.join(PARENT_DIR, "static")
    db_dir = os.path.join(tmp_dir, "images") # nơi chứa ảnh gốc để so sánh 
    file_path_vectorDatabase = os.path.join(PARENT_DIR, "instance", "faiss_index.index")
    file_path_metadata = os.path.join(PARENT_DIR, "instance", "metadata.json")

    
    #db_dir = "static/images" # nơi chứa ảnh gốc để so sánh 
    db_embeddings = []
    db_names = []

    print("Embedding")
    for fname in os.listdir(db_dir):
        path = os.path.join(db_dir, fname)
        emb = get_image_embedding(path)
        db_embeddings.append(emb)
        db_names.append(fname)
    #==========================================================
    # WARNING:
    #Nếu này mà lên vài nghìn ảnh thì ... rip RAM
    #====================
    db_embeddings = torch.cat(db_embeddings, dim=0)

    # === Add mọi thứ vào một database vector ===
    db_embeddings_np = db_embeddings.cpu().numpy().astype('float32')

    dim = db_embeddings_np.shape[1] 
    index = faiss.IndexFlatL2(dim)
    index.add(db_embeddings_np) #Tạo database
    faiss.write_index(index, file_path_vectorDatabase)

    index_to_name = {i: db_names[i] for i in range(len(db_names))}

    #===  metadata (địa điểm) ===
    with open(file_path_metadata, "w", encoding="utf-8") as f:
        json.dump(index_to_name, f)



if __name__ == "__main__":
    main()
