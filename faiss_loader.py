import faiss
from models_loader import sbert_model
from models import FaissMapping
from extensions import db
from flask import current_app
import os

faiss_Text_index = None
index_to_image_id = None

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
file_path_vectorDatabase = os.path.join(BASE_DIR, "instance", "PlaceDescriptionFaiss.bin")

#Các description và name được encode
def get_faiss_Text_index():
    return faiss_Text_index

def get_index_to_image_id():
    return index_to_image_id


def load_faiss_index(faiss_file=file_path_vectorDatabase):

    global faiss_Text_index, index_to_image_id

    app = current_app._get_current_object()
    with app.app_context():


        # Load FAISS index
        faiss_Text_index = faiss.read_index(faiss_file)

        # Load mapping: FAISS index to image_id in database
        mappings = FaissMapping.query.order_by(FaissMapping.id).all()
        index_to_image_id = {m.id: m.image_id for m in mappings}

        if len(index_to_image_id) < 1:
            print("Lỗi load index to image_id(db)")
        elif faiss_Text_index.ntotal < 1:
            print("Lỗi load FAISS index")
