# schemas.py — Pydantic v2 Models and Enums for Content Enrichment API

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, HttpUrl


class CategoryEnum(str, Enum):
    ENGINEERING = "engineering"
    AI_ML = "ai_ml"
    DEVOPS_CLOUD = "devops_cloud"
    SECURITY = "security"
    OTHER = "other"


class DepthEnum(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class FlagEnum(str, Enum):
    CONTAINS_CODE = "contains_code"
    OUTDATED_INFO = "outdated_info"
    PROMOTIONAL_SPAM = "promotional_spam"
    NEEDS_REVIEW = "needs_review"


class EnrichRequest(BaseModel):
    text: str = Field(
        ...,
        min_length=10,
        max_length=3000,
        description="Raw technical text or scraped record content to enrich.",
        examples=["We migrated our PostgreSQL database cluster to Kubernetes using Zalando operator."]
    )
    source_url: Optional[str] = Field(
        default=None,
        description="Optional source URL of the scraped record."
    )


class EnrichResponse(BaseModel):
    category: CategoryEnum = Field(..., description="Target category from closed Enum list.")
    summary: str = Field(..., description="One concise sentence thesis summary.")
    technical_depth: DepthEnum = Field(..., description="Estimated technical complexity depth.")
    quality_flags: List[FlagEnum] = Field(default_factory=list, description="Array of quality or review flags.")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0.")
    reason: str = Field(..., description="One short sentence explaining the category assignment.")


class ResponseMeta(BaseModel):
    prompt_version: str = "v1"
    model_id: str = "openrouter/free"
    duration_ms: int
    input_tokens: int
    output_tokens: int
    cost_micro_cents: int
    repair_count: int = 0
    stub_mode: bool = False
    kill_switch_active: bool = False


class APIResponseEnvelope(BaseModel):
    status: str = "success"
    data: EnrichResponse
    meta: ResponseMeta


class ErrorDetail(BaseModel):
    code: str
    message: str
    field: Optional[str] = None
    details: Optional[dict] = None


class ErrorEnvelope(BaseModel):
    error: ErrorDetail


class CostLogEntry(BaseModel):
    timestamp: str
    prompt_version: str
    model_id: str
    input_tokens: int
    output_tokens: int
    cost_micro_cents: int
    duration_ms: int
    repair_count: int
    status: str
