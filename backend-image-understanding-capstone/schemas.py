# schemas.py — Pydantic Validation Schemas for Image Matching Platform

from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


# ------------------------------------------------------------------------------
# Vision & Ingestion Schemas
# ------------------------------------------------------------------------------

class ImageTagSchema(BaseModel):
    subject: str = Field(..., min_length=2, max_length=128, description="Primary subject (e.g., 'red fox')")
    category: str = Field(..., min_length=2, max_length=64, description="High-level category (e.g., 'animal')")
    attributes: List[str] = Field(default_factory=list, description="Visual descriptive attributes")
    caption: str = Field(..., min_length=5, max_length=1000, description="Full descriptive caption")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Model confidence score between 0 and 1")


class ImageIngestRequest(BaseModel):
    id: str = Field(..., min_length=1, max_length=64)
    filename: str = Field(..., min_length=1, max_length=256)
    url: Optional[str] = None
    mock_data: Optional[Dict[str, Any]] = None


class DirectMatchRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=256)
    content: str = Field(..., min_length=10)
    target_subject: str = Field(..., min_length=2, max_length=128)


class ImageItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    filename: str
    subject: str
    category: str
    attributes: List[str]
    caption: str
    confidence: float
    status: str
    created_at: datetime


# ------------------------------------------------------------------------------
# Blog Post & Matching Schemas
# ------------------------------------------------------------------------------

class BlogPostCreate(BaseModel):
    id: str = Field(..., min_length=1, max_length=64)
    title: str = Field(..., min_length=5, max_length=256)
    content: str = Field(..., min_length=10)
    target_subject: str = Field(..., min_length=2, max_length=128)


class BlogPostResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    content: str
    target_subject: str
    created_at: datetime


class MatchCandidate(BaseModel):
    image_id: str
    filename: str
    subject: str
    category: str
    caption: str
    similarity_score: float
    confidence: float
    guard_passed: bool
    guard_verdict: str  # 'ACCEPTED', 'REFUSED'
    guard_reason: str


class PostMatchesResponse(BaseModel):
    post_id: str
    post_title: str
    target_subject: str
    has_confident_match: bool
    status_summary: str
    candidates: List[MatchCandidate]


# ------------------------------------------------------------------------------
# Review API Schemas
# ------------------------------------------------------------------------------

class ReviewRequest(BaseModel):
    post_id: str
    image_id: str
    reason: Optional[str] = "Editorial review"


class ReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    post_id: str
    image_id: str
    decision: str
    reason: Optional[str]
    similarity_score: float
    created_at: datetime


# ------------------------------------------------------------------------------
# Telemetry & Cost Schemas
# ------------------------------------------------------------------------------

class CostLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    operation: str
    model_id: str
    input_tokens: int
    output_tokens: int
    cost_micro_cents: int
    duration_ms: int
    created_at: datetime


# ------------------------------------------------------------------------------
# Error Envelope
# ------------------------------------------------------------------------------

class ErrorDetail(BaseModel):
    code: str
    message: str
    field: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class ErrorEnvelope(BaseModel):
    error: ErrorDetail
