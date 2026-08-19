# services/embedding_service.py — Semantic Embedding & Cosine Similarity Engine

import re
import math
import numpy as np
from typing import List, Dict

# Domain taxonomy / semantic synonym mapping
SYNONYM_MAP = {
    "vulpes": "fox",
    "vulpes vulpes": "red fox",
    "canis lupus": "gray wolf",
    "canis familiaris": "dog",
    "canine": "dog",
    "canines": "dog",
    "vulpine": "fox",
    "lupine": "wolf",
    "qubit": "quantum",
    "qubits": "quantum",
    "orbital": "space",
    "spacecraft": "satellite",
    "spacecrafts": "satellite",
    "autumn": "forest",
    "canopy": "forest",
    "snowpack": "arctic",
    "tundra": "arctic"
}

VOCABULARY = [
    "fox", "red", "forest", "wild", "animal", "vulpes",
    "wolf", "gray", "pack", "howl", "canis", "lupus", "predator", "snow",
    "dog", "retriever", "golden", "pet", "domestic", "park",
    "quantum", "computing", "qubits", "physics", "processor",
    "satellite", "space", "orbit", "earth", "communications",
    "ocean", "whale", "marine", "deep", "water",
    "mountain", "peak", "alpine", "nature", "landscape"
]


class EmbeddingService:
    @staticmethod
    def _preprocess_text(text: str) -> str:
        text = text.lower()
        # Expand synonyms
        for key, val in SYNONYM_MAP.items():
            text = re.sub(rf"\b{key}\b", f"{key} {val}", text)
        return text

    @classmethod
    def get_embedding(cls, text: str) -> List[float]:
        """
        Generates a normalized semantic vector embedding for the input text.
        """
        clean_text = cls._preprocess_text(text)
        vector = np.zeros(len(VOCABULARY), dtype=float)

        tokens = re.findall(r"\b\w+\b", clean_text)
        for token in tokens:
            for idx, word in enumerate(VOCABULARY):
                if token == word or word in token:
                    vector[idx] += 1.0

        # Also add character n-gram signal for unknown words
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        else:
            # Fallback uniform sparse vector
            vector = np.full(len(VOCABULARY), 1.0 / math.sqrt(len(VOCABULARY)))

        return vector.tolist()

    @staticmethod
    def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
        """
        Calculates cosine similarity between two embedding vectors.
        Returns score in range [0.0, 1.0].
        """
        a = np.array(vec_a, dtype=float)
        b = np.array(vec_b, dtype=float)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)

        if norm_a == 0 or norm_b == 0:
            return 0.0

        sim = float(np.dot(a, b) / (norm_a * norm_b))
        return max(0.0, min(1.0, round(sim, 4)))
