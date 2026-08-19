# services/mismatch_guard.py — Production Safety Layer & Mismatch Guard

import os
from typing import Tuple, Dict, Any

# Conflicting subject entities that must never be confused
CONFLICT_PAIRS = {
    "fox": ["wolf", "dog", "coyote", "jackal", "cat", "satellite", "computer"],
    "red fox": ["gray wolf", "wolf", "dog", "coyote", "satellite", "computer"],
    "wolf": ["fox", "dog", "retriever", "satellite", "computer"],
    "gray wolf": ["red fox", "fox", "dog", "retriever", "satellite", "computer"],
    "dog": ["fox", "wolf", "coyote", "satellite", "computer"],
    "quantum computing": ["satellite", "fox", "wolf", "dog", "ocean"],
    "space satellite": ["quantum computing", "fox", "wolf", "dog", "ocean"]
}


class MismatchGuard:
    def __init__(self, similarity_threshold: float = None, min_confidence: float = None):
        self.similarity_threshold = similarity_threshold or float(os.getenv("MATCH_THRESHOLD", "0.72"))
        self.min_confidence = min_confidence or float(os.getenv("MIN_CONFIDENCE", "0.75"))

    def evaluate_candidate(
        self,
        post_target_subject: str,
        post_title: str,
        image_subject: str,
        image_category: str,
        image_caption: str,
        similarity_score: float,
        model_confidence: float
    ) -> Tuple[bool, str, str]:
        """
        Evaluates a candidate image against the post.
        Returns: (guard_passed: bool, verdict: str ('ACCEPTED'|'REFUSED'), reason: str)
        """
        post_subj_lower = post_target_subject.lower()
        img_subj_lower = image_subject.lower()

        # Guard Rule 1: Model Confidence Check
        if model_confidence < self.min_confidence:
            return False, "REFUSED", f"Low model confidence ({model_confidence:.2f} < {self.min_confidence:.2f}). Flagged for human review."

        # Guard Rule 2: Similarity Score Threshold Gating
        if similarity_score < self.similarity_threshold:
            return False, "REFUSED", f"Similarity score ({similarity_score:.2f}) below confidence threshold ({self.similarity_threshold:.2f})."

        # Guard Rule 3: Entity Conflict & Subject Mismatch Guard (The Fox vs. Wolf Test)
        for key, conflicts in CONFLICT_PAIRS.items():
            if key in post_subj_lower:
                for conflict in conflicts:
                    if conflict in img_subj_lower or conflict in image_caption.lower():
                        # Conflict detected!
                        return False, "REFUSED", f"Subject mismatch: article discusses '{post_target_subject}' whereas candidate image depicts '{image_subject}'."

        # Passed all guard rails!
        return True, "ACCEPTED", f"High semantic relevance ({similarity_score:.2f}) matching topic '{post_target_subject}'."
