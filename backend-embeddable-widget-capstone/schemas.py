# schemas.py — Pydantic Validation Schemas for Widget Platform

from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from datetime import datetime


# ------------------------------------------------------------------------------
# Widget Admin Schemas
# ------------------------------------------------------------------------------

class FieldConfig(BaseModel):
    name: str
    type: str = "text"
    label: str
    required: bool = True


class WidgetCreateRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=256)
    description: str = Field(..., min_length=2, max_length=512)
    button_text: str = Field("Submit", min_length=1, max_length=64)
    theme_color: str = Field("#4f46e5", max_length=32)
    allowed_origins: str = Field("*", max_length=512)
    fields_config: Optional[List[FieldConfig]] = None


class WidgetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    title: str
    description: str
    button_text: str
    theme_color: str
    allowed_origins: str
    fields_config: List[Dict[str, Any]]
    created_at: datetime


class WidgetPublicConfigResponse(BaseModel):
    widget_id: str
    title: str
    description: str
    button_text: str
    theme_color: str
    fields_config: List[Dict[str, Any]]
    submit_url: str


# ------------------------------------------------------------------------------
# Submission Schemas
# ------------------------------------------------------------------------------

class SubmissionCreateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    widget_id: str = Field(..., min_length=1, max_length=64)
    name: str = Field(..., min_length=1, max_length=128)
    email: EmailStr = Field(...)
    message: Optional[str] = Field(None, max_length=3000)
    website_url_hp: Optional[str] = Field(
        default="",
        alias="_website_url_hp",
        description="Hidden honeypot field. Must be empty for legitimate human submissions."
    )


class SubmissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    widget_id: str
    status: str = "received"
    message: str = "Submission received successfully."
    country: Optional[str] = None
    city: Optional[str] = None
    geo_enriched: bool = False
    created_at: datetime


# ------------------------------------------------------------------------------
# Analytics Schemas
# ------------------------------------------------------------------------------

class AnalyticsStatsResponse(BaseModel):
    tenant_id: str
    total_widgets: int
    total_submissions: int
    spam_blocked_count: int
    recent_submissions: List[Dict[str, Any]]


class GeoAnalyticsResponse(BaseModel):
    tenant_id: str
    country_breakdown: Dict[str, int]
    top_cities: List[Dict[str, Any]]


# ------------------------------------------------------------------------------
# Error Schemas
# ------------------------------------------------------------------------------

class ErrorDetail(BaseModel):
    code: str
    message: str
    field: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class ErrorEnvelope(BaseModel):
    error: ErrorDetail
