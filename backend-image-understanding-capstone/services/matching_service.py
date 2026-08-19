# services/matching_service.py — Semantic Vector Ranking & Safety Evaluation Service

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from models import ImageItem, BlogPost
from schemas import MatchCandidate, PostMatchesResponse
from services.embedding_service import EmbeddingService
from services.mismatch_guard import MismatchGuard


class MatchingService:
    def __init__(self):
        self.guard = MismatchGuard()

    def rank_and_evaluate_matches(self, db: Session, post_id: str) -> Optional[PostMatchesResponse]:
        post = db.query(BlogPost).filter(BlogPost.id == post_id).first()
        if not post:
            return None

        # Compute or retrieve post embedding
        post_vector = post.embedding
        if not post_vector:
            post_vector = EmbeddingService.get_embedding(f"{post.title} {post.content} {post.target_subject}")
            post.embedding = post_vector
            db.commit()

        # Fetch all candidate images
        images = db.query(ImageItem).all()
        scored_candidates: List[Dict[str, Any]] = []

        for img in images:
            img_vector = img.embedding
            if not img_vector:
                img_vector = EmbeddingService.get_embedding(f"{img.subject} {img.category} {' '.join(img.attributes)} {img.caption}")
                img.embedding = img_vector
                db.commit()

            similarity = EmbeddingService.cosine_similarity(post_vector, img_vector)

            # Pass through Mismatch Guard
            passed, verdict, reason = self.guard.evaluate_candidate(
                post_target_subject=post.target_subject,
                post_title=post.title,
                image_subject=img.subject,
                image_category=img.category,
                image_caption=img.caption,
                similarity_score=similarity,
                model_confidence=img.confidence
            )

            scored_candidates.append({
                "image_id": img.id,
                "filename": img.filename,
                "subject": img.subject,
                "category": img.category,
                "caption": img.caption,
                "similarity_score": similarity,
                "confidence": img.confidence,
                "guard_passed": passed,
                "guard_verdict": verdict,
                "guard_reason": reason
            })

        # Sort by similarity score descending
        scored_candidates.sort(key=lambda x: x["similarity_score"], reverse=True)

        candidates_models = [MatchCandidate(**c) for c in scored_candidates]

        has_confident_match = len(candidates_models) > 0 and candidates_models[0].guard_passed

        if has_confident_match:
            top = candidates_models[0]
            status_summary = f"Confident match identified: '{top.filename}' ({top.subject}) with similarity score {top.similarity_score:.2f}."
        else:
            if candidates_models:
                status_summary = f"No confident match found. Top candidate '{candidates_models[0].filename}' refused: {candidates_models[0].guard_reason}"
            else:
                status_summary = "No candidate images available in corpus."

        return PostMatchesResponse(
            post_id=post.id,
            post_title=post.title,
            target_subject=post.target_subject,
            has_confident_match=has_confident_match,
            status_summary=status_summary,
            candidates=candidates_models
        )
