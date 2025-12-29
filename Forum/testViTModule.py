import os
import torch
from PIL import Image
from transformers import AutoModelForImageClassification, ViTImageProcessor

# ==============================
# LOAD MODEL (chỉ load 1 lần)
# ==============================
print(" Đang tải model NSFW...")
model = AutoModelForImageClassification.from_pretrained("Falconsai/nsfw_image_detection")
processor = ViTImageProcessor.from_pretrained("Falconsai/nsfw_image_detection")
print(" Model loaded thành công!")

# ==============================
# HÀM CHECK NSFW
# ==============================
def check_nsfw(image_path):
    if not os.path.exists(image_path):
        print(" Ảnh không tồn tại:", image_path)
        return

    try:
        img = Image.open(image_path).convert("RGB")
    except:
        print(" File không phải ảnh hợp lệ:", image_path)
        return

    # Tiền xử lý và dự đoán
    inputs = processor(images=img, return_tensors="pt")

    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits
        probs = logits.softmax(dim=-1)[0]

    # Kết quả dự đoán
    labels = model.config.id2label
    pred_idx = logits.argmax(-1).item()
    pred_label = labels[pred_idx]

    print("\n=====  Kết quả phân loại =====")
    print(f"Ảnh: {image_path}")
    print(f" Label dự đoán: {pred_label.upper()}")
    print(f" NSFW Score: {probs[1]:.4f}")
    print(f" NORMAL Score: {probs[0]:.4f}")

    if pred_label == "nsfw":
        print(" KẾT LUẬN: ẢNH KHÔNG AN TOÀN (NSFW) ")
    else:
        print(" KẾT LUẬN: ẢNH AN TOÀN ")

# ==============================
# MAIN TEST
# ==============================
if __name__ == "__main__":
    image_path = "map.png"
    check_nsfw(image_path)
