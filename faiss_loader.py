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

    # Load FAISS index từ file và SBERT model.
    # Đồng thời load mapping index -> image_id từ database.

    global faiss_Text_index, index_to_image_id

    app = current_app._get_current_object()
    with app.app_context():


        # Load FAISS index
        print(f"Loading FAISS index từ {faiss_file} ...")
        faiss_Text_index = faiss.read_index(faiss_file)

        # Load mapping từ FAISS index image_id từ database
        mappings = FaissMapping.query.order_by(FaissMapping.id).all()
        index_to_image_id = {m.id: m.image_id for m in mappings}

        print(f"FAISS index và mapping đã load. Số lượng record: {len(index_to_image_id)}")
        print("FAISS ntotal:", faiss_Text_index.ntotal)
        print("Mapping size:", len(index_to_image_id))
