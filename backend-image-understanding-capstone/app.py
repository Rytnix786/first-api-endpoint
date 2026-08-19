# app.py — FastAPI Application for AI Image Understanding & Content Matching Engine

from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List

from models import Base, ImageItem, BlogPost, ReviewLog, CostLog
from database import init_db, get_db
from schemas import (
    ImageItemResponse,
    ImageIngestRequest,
    DirectMatchRequest,
    BlogPostCreate,
    BlogPostResponse,
    PostMatchesResponse,
    ReviewRequest,
    ReviewResponse,
    CostLogResponse,
    ErrorEnvelope,
    ErrorDetail
)
from services.matching_service import MatchingService
from services.embedding_service import EmbeddingService

app = FastAPI(
    title="AI Image Understanding & Content Matching Engine API",
    description="Structured vision tagging, vector similarity ranking, and production mismatch guard rejecting incorrect recommendations.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

matching_service = MatchingService()


@app.on_event("startup")
def on_startup():
    init_db()


# ------------------------------------------------------------------------------
# Custom Validation Exception Handler (HTTP 400)
# ------------------------------------------------------------------------------

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    first_error = errors[0] if errors else {}
    loc = first_error.get("loc", [])
    field_name = str(loc[-1]) if loc else "body"
    msg = first_error.get("msg", "Invalid input data.")

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=ErrorEnvelope(
            error=ErrorDetail(
                code="invalid_payload",
                message=f"Validation failed on field '{field_name}': {msg}",
                field=field_name,
                details={"validation_errors": errors}
            )
        ).model_dump()
    )


# ------------------------------------------------------------------------------
# 1. Matching & Mismatch Guard Endpoints
# ------------------------------------------------------------------------------

@app.get("/api/v1/posts/{post_id}/matches", response_model=PostMatchesResponse, tags=["Matching Engine"])
def get_post_image_matches(post_id: str, db: Session = Depends(get_db)):
    """
    Ranks candidate images for a blog post using semantic vector similarity,
    evaluates each candidate with the production Mismatch Guard, and returns
    reasons for approvals or refusals.
    """
    result = matching_service.rank_and_evaluate_matches(db, post_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Blog post '{post_id}' not found."
        )
    return result


# ------------------------------------------------------------------------------
# 2. Editorial Review & Audit Trail Endpoints
# ------------------------------------------------------------------------------

@app.get("/api/v1/reviews", response_model=List[ReviewResponse], tags=["Editorial Review"])
def list_reviews(db: Session = Depends(get_db)):
    """Returns the editorial approval and rejection audit trail."""
    return db.query(ReviewLog).order_by(ReviewLog.created_at.desc()).all()


@app.post("/api/v1/reviews/approve", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED, tags=["Editorial Review"])
def approve_recommendation(payload: ReviewRequest, db: Session = Depends(get_db)):
    """Records editorial approval for a post-image recommendation."""
    post = db.query(BlogPost).filter(BlogPost.id == payload.post_id).first()
    image = db.query(ImageItem).filter(ImageItem.id == payload.image_id).first()

    if not post or not image:
        raise HTTPException(status_code=404, detail="Post or Image not found.")

    similarity = EmbeddingService.cosine_similarity(post.embedding or [], image.embedding or [])

    review = ReviewLog(
        post_id=post.id,
        image_id=image.id,
        decision="approved",
        reason=payload.reason or "Approved by editor",
        similarity_score=similarity
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


@app.post("/api/v1/reviews/reject", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED, tags=["Editorial Review"])
def reject_recommendation(payload: ReviewRequest, db: Session = Depends(get_db)):
    """Records editorial rejection for a post-image recommendation."""
    post = db.query(BlogPost).filter(BlogPost.id == payload.post_id).first()
    image = db.query(ImageItem).filter(ImageItem.id == payload.image_id).first()

    if not post or not image:
        raise HTTPException(status_code=404, detail="Post or Image not found.")

    similarity = EmbeddingService.cosine_similarity(post.embedding or [], image.embedding or [])

    review = ReviewLog(
        post_id=post.id,
        image_id=image.id,
        decision="rejected",
        reason=payload.reason or "Rejected by editor",
        similarity_score=similarity
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


# ------------------------------------------------------------------------------
# 3. Image & Post Ingestion Endpoints
# ------------------------------------------------------------------------------

@app.post("/api/v1/images/ingest", response_model=ImageItemResponse, status_code=status.HTTP_201_CREATED, tags=["Images"])
def ingest_image(payload: ImageIngestRequest, db: Session = Depends(get_db)):
    """
    Ingests an image into the understanding pipeline:
    1. Extracts structured tags and caption via VisionService.
    2. Validates against ImageTagSchema.
    3. Flags low-confidence classifications (< 0.70).
    4. Computes semantic embedding vector.
    5. Records cost telemetry.
    """
    from services.vision_service import VisionService
    vision_service = VisionService()

    validated_tags, in_tok, out_tok, cost_uc = vision_service.process_image(payload.filename, payload.mock_data)

    embedding = EmbeddingService.get_embedding(
        f"{validated_tags.subject} {validated_tags.category} {' '.join(validated_tags.attributes)} {validated_tags.caption}"
    )
    img_status = "flagged_low_confidence" if validated_tags.confidence < 0.70 else "processed"

    existing = db.query(ImageItem).filter(ImageItem.id == payload.id).first()
    if existing:
        db.delete(existing)
        db.commit()

    image = ImageItem(
        id=payload.id,
        filename=payload.filename,
        url=payload.url,
        subject=validated_tags.subject,
        category=validated_tags.category,
        attributes=validated_tags.attributes,
        caption=validated_tags.caption,
        confidence=validated_tags.confidence,
        embedding=embedding,
        status=img_status
    )
    db.add(image)

    # Telemetry Cost Log
    cost = CostLog(
        operation="vision_ingestion",
        model_id=vision_service.model_id,
        input_tokens=in_tok,
        output_tokens=out_tok,
        cost_micro_cents=cost_uc,
        duration_ms=350
    )
    db.add(cost)
    db.commit()
    db.refresh(image)
    return image


@app.get("/api/v1/images", response_model=List[ImageItemResponse], tags=["Images"])
def list_images(db: Session = Depends(get_db)):
    return db.query(ImageItem).all()


@app.get("/api/v1/posts", response_model=List[BlogPostResponse], tags=["Posts"])
def list_posts(db: Session = Depends(get_db)):
    return db.query(BlogPost).all()


@app.post("/api/v1/posts", response_model=BlogPostResponse, status_code=status.HTTP_201_CREATED, tags=["Posts"])
def create_post(payload: BlogPostCreate, db: Session = Depends(get_db)):
    existing = db.query(BlogPost).filter(BlogPost.id == payload.id).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Post '{payload.id}' already exists.")

    embedding = EmbeddingService.get_embedding(f"{payload.title} {payload.content} {payload.target_subject}")

    post = BlogPost(
        id=payload.id,
        title=payload.title,
        content=payload.content,
        target_subject=payload.target_subject,
        embedding=embedding
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


# ------------------------------------------------------------------------------
# 4. Direct Ad-Hoc Content Matching Endpoint
# ------------------------------------------------------------------------------

@app.post("/api/v1/match/direct", response_model=PostMatchesResponse, tags=["Matching Engine"])
def direct_content_match(payload: DirectMatchRequest, db: Session = Depends(get_db)):
    """
    Ranks images for ad-hoc blog post text without persisting a blog post record.
    """
    post_vector = EmbeddingService.get_embedding(f"{payload.title} {payload.content} {payload.target_subject}")
    images = db.query(ImageItem).all()
    scored_candidates = []

    for img in images:
        img_vector = img.embedding or EmbeddingService.get_embedding(f"{img.subject} {img.category} {' '.join(img.attributes)} {img.caption}")
        similarity = EmbeddingService.cosine_similarity(post_vector, img_vector)

        passed, verdict, reason = matching_service.guard.evaluate_candidate(
            post_target_subject=payload.target_subject,
            post_title=payload.title,
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

    scored_candidates.sort(key=lambda x: x["similarity_score"], reverse=True)
    from schemas import MatchCandidate
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
        post_id="adhoc_query",
        post_title=payload.title,
        target_subject=payload.target_subject,
        has_confident_match=has_confident_match,
        status_summary=status_summary,
        candidates=candidates_models
    )


# ------------------------------------------------------------------------------
# 5. Telemetry & Cost Logs
# ------------------------------------------------------------------------------

@app.get("/api/v1/costs", response_model=List[CostLogResponse], tags=["Telemetry"])
def list_costs(db: Session = Depends(get_db)):
    return db.query(CostLog).order_by(CostLog.created_at.desc()).all()


# ------------------------------------------------------------------------------
# Health Check
# ------------------------------------------------------------------------------

@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": "AI Image Understanding & Content Matching Engine",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
