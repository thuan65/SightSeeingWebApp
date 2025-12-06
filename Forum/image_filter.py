import os
import torch
from PIL import Image
from transformers import AutoModelForImageClassification, ViTImageProcessor

print("⏳ Loading Falconsai NSFW model...")
model = AutoModelForImageClassification.from_pretrained("Falconsai/nsfw_image_detection")
processor = ViTImageProcessor.from_pretrained("Falconsai/nsfw_image_detection")
print("🚀 NSFW model is ready!")

def is_nsfw_image(image_path, threshold=0.75):
    """
    True  => NSFW (block)
    False => SAFE (allow)
    """
    if not os.path.exists(image_path):
        return True, {"error": "File not found"}

    try:
        img = Image.open(image_path).convert("RGB")
    except:
        return True, {"error": "Invalid image"}

    inputs = processor(images=img, return_tensors="pt")

    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits
        probs = logits.softmax(dim=-1)[0]

    labels = model.config.id2label
    pred = labels[logits.argmax(-1).item()]
    score = float(probs[1])

    info = {
        "label": pred,
        "nsfw_score": score
    }

    blocked = (pred == "nsfw") or (score >= threshold)
    return blocked, info
