import faiss
import numpy as np
from models_loader import sbert_model
from models import Image, FaissMapping
from extensions import db
from __init__ import create_app

def generate_embeddings_to_db():
    app = create_app()
    with app.app_context():
        # Clear old mapping
        FaissMapping.query.delete()
        db.session.commit()

        images = Image.query.all()
        sentences = [f"{img.name} - {img.description}" for img in images]

        embeddings = sbert_model.encode(sentences, convert_to_numpy=True).astype('float32')

        # Save mapping
        for idx, img in enumerate(images):
            db.session.add(FaissMapping(id=idx, image_id=img.id))
        db.session.commit()

        return embeddings

def build_faiss_index(file_path="faiss_index.bin"):
    embeddings = generate_embeddings_to_db()
    faiss.normalize_L2(embeddings)
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)
    faiss.write_index(index, file_path)
    print(f"FAISS index created: {file_path}, total vectors: {index.ntotal}")

if __name__ == "__main__":
    build_faiss_index()
