from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import cv2
import numpy as np


@dataclass
class EmotionResult:
    emotion: str
    confidence: float
    region: dict[str, int] | None = None


class EmotionAnalyzer:
    _BEIT_FALLBACK_LABELS = {
        0: "angry",
        1: "disgust",
        2: "fear",
        3: "happy",
        4: "sad",
        5: "surprise",
        6: "neutral",
    }

    def __init__(self, backend: str = "deepface") -> None:
        self.backend = backend.lower().strip()
        if self.backend == "deepface":
            from deepface import DeepFace

            self._deepface = DeepFace
        elif self.backend == "beit":
            import torch
            from PIL import Image
            from transformers import BeitForImageClassification, BeitImageProcessor

            self._torch = torch
            self._pil_image = Image
            self._processor = BeitImageProcessor.from_pretrained(
                "Tanneru/Facial-Emotion-Detection-FER-RAFDB-AffectNet-BEIT-Large"
            )
            self._model = BeitForImageClassification.from_pretrained(
                "Tanneru/Facial-Emotion-Detection-FER-RAFDB-AffectNet-BEIT-Large"
            )
            self._model.eval()
        else:
            raise ValueError("Unsupported backend. Use 'deepface' or 'beit'.")

    def analyze(self, frame: np.ndarray) -> EmotionResult:
        if self.backend == "deepface":
            return self._analyze_deepface(frame)
        return self._analyze_beit(frame)

    def _analyze_deepface(self, frame: np.ndarray) -> EmotionResult:
        result = self._deepface.analyze(
            frame,
            actions=["emotion"],
            enforce_detection=False,
            detector_backend="opencv",
        )
        face = self._extract_face_result(result)
        emotion = self._extract_dominant_emotion(result)
        confidence = self._extract_confidence(face, emotion)
        region = self._extract_region(face)
        return EmotionResult(emotion=emotion, confidence=confidence, region=region)

    def _analyze_beit(self, frame: np.ndarray) -> EmotionResult:
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = self._pil_image.fromarray(rgb)
        inputs = self._processor(images=image, return_tensors="pt")
        with self._torch.no_grad():
            outputs = self._model(**inputs)
            probabilities = self._torch.softmax(outputs.logits, dim=-1)[0]
            predicted_class = int(probabilities.argmax().item())
            confidence = float(probabilities[predicted_class].item() * 100.0)
        raw_label = str(self._model.config.id2label.get(predicted_class, f"label_{predicted_class}"))
        emotion = self._normalize_beit_label(raw_label, predicted_class)
        return EmotionResult(emotion=emotion, confidence=confidence, region=None)

    def _normalize_beit_label(self, label: str, predicted_class: int) -> str:
        clean = label.strip().lower().replace(" ", "_")

        if clean in {"happiness", "joy"}:
            return "happy"
        if clean in {"sadness"}:
            return "sad"
        if clean in {"anger"}:
            return "angry"

        if clean.startswith("label_"):
            return self._BEIT_FALLBACK_LABELS.get(predicted_class, clean)

        return clean

    @staticmethod
    def _extract_face_result(result: Any) -> dict[str, Any]:
        if isinstance(result, list) and result and isinstance(result[0], dict):
            return result[0]
        if isinstance(result, dict):
            return result
        return {}

    @staticmethod
    def _extract_dominant_emotion(result: Any) -> str:
        if isinstance(result, list) and result and isinstance(result[0], dict):
            return str(result[0].get("dominant_emotion", "unknown"))
        if isinstance(result, dict):
            return str(result.get("dominant_emotion", "unknown"))
        return "unknown"

    @staticmethod
    def _extract_confidence(face_result: dict[str, Any], emotion: str) -> float:
        emotion_scores = face_result.get("emotion", {})
        if isinstance(emotion_scores, dict):
            value = emotion_scores.get(emotion, 0.0)
            try:
                return float(value)
            except (TypeError, ValueError):
                return 0.0
        return 0.0

    @staticmethod
    def _extract_region(face_result: dict[str, Any]) -> dict[str, int] | None:
        region = face_result.get("region", {})
        if not isinstance(region, dict):
            return None

        try:
            x = int(region.get("x", 0))
            y = int(region.get("y", 0))
            w = int(region.get("w", 0))
            h = int(region.get("h", 0))
        except (TypeError, ValueError):
            return None

        if w <= 0 or h <= 0:
            return None

        return {"x": x, "y": y, "w": w, "h": h}
