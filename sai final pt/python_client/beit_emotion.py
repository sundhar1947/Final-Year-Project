from argparse import ArgumentParser
from pathlib import Path

from PIL import Image
from transformers import BeitForImageClassification, BeitImageProcessor

MODEL_ID = "Tanneru/Facial-Emotion-Detection-FER-RAFDB-AffectNet-BEIT-Large"


def predict_emotion(image_path: Path) -> str:
    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    image = Image.open(image_path).convert("RGB")

    processor = BeitImageProcessor.from_pretrained(MODEL_ID)
    model = BeitForImageClassification.from_pretrained(MODEL_ID)

    inputs = processor(images=image, return_tensors="pt")
    outputs = model(**inputs)
    predicted_class = outputs.logits.argmax(-1).item()
    return model.config.id2label[predicted_class]


def main() -> None:
    parser = ArgumentParser(description="Predict facial emotion from an image using BEiT model")
    parser.add_argument("image", type=Path, help="Path to the input image")
    args = parser.parse_args()

    emotion = predict_emotion(args.image)
    print(f"Predicted emotion: {emotion}")


if __name__ == "__main__":
    main()
