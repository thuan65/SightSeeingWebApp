import time

start = time.time()

from sentence_transformers import SentenceTransformer
from transformers import CLIPProcessor, CLIPModel

# === Load model ===
sbert_model  = SentenceTransformer("keepitreal/vietnamese-sbert")


Clip_model = "openai/clip-vit-base-patch32"
model = CLIPModel.from_pretrained(Clip_model)
#processor = CLIPProcessor.from_pretrained(Clip_model)#Slower
processor = CLIPProcessor.from_pretrained(Clip_model, use_fast=True)#For faster run app
# dùng cho kiểm tra toxicity của forum & feedback
EN_MODEL = "unitary/toxic-bert"
VI_MODEL = "visolex/phobert-hsd"

end = time.time()

print("Thời gian chạy:", end - start, "giây")