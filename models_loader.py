from sentence_transformers import SentenceTransformer

sbert_model  = SentenceTransformer("keepitreal/vietnamese-sbert")
# dùng cho kiểm tra toxicity của forum & feedback
EN_MODEL = "unitary/toxic-bert"
VI_MODEL = "visolex/phobert-hsd"