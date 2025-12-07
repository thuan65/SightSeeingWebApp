import sys, os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR) #Ra 1 cấp thư mục
# Thêm thư mục cha vào sys.path
sys.path.append(PARENT_DIR)
from models_loader import Clip_model, processor, model
import faiss
from PIL import Image
import torch, os, json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR) #Ra 1 cấp thư mục 
file_path_vectorDatabase = os.path.join(PARENT_DIR, "instance", "a.index")
index = faiss.read_index(file_path_vectorDatabase)
file_path_metadata = os.path.join(PARENT_DIR, "instance", "metadata.json")

with open(file_path_metadata, "r") as f:
    index_to_name = json.load(f)

def get_image_embedding(image_path):
    image = Image.open(image_path).convert("RGB")
    inputs = processor(images=image, return_tensors="pt")
    with torch.no_grad():
        emb = model.get_image_features(**inputs)
    return emb / emb.norm(dim=-1, keepdim=True)

def find_similar(image_query_path, k=5):
    # Lấy embedding của ảnh query
    query_vector = get_image_embedding(image_query_path).cpu().numpy().astype('float32')

    # FAISS search
    distances, indices = index.search(query_vector, k=k)

    # Map FAISS index -> tên file
    results = []
    for rank in range(k):
        faiss_idx = int(indices[0][rank])
        file_name = index_to_name[str(faiss_idx)]
        score = float(distances[0][rank])
        results.append({
            "rank": rank + 1,
            "file_name": file_name,
            "distance": score
        })

    return results


def main():

    ret = find_similar("static/ThuNghiem.jpg")
    print(ret)
    pass


if __name__ == "__main__":
    main()