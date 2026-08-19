# app.py — FastAPI Embeddable Widget & Lead-Capture Platform Microservice

import os
from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException, Header, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from models import Base, Tenant, Widget, Submission
from database import engine, init_db, get_db
from schemas import (
    WidgetCreateRequest,
    WidgetResponse,
    WidgetPublicConfigResponse,
    SubmissionCreateRequest,
    SubmissionResponse,
    AnalyticsStatsResponse,
    GeoAnalyticsResponse,
    ErrorEnvelope,
    ErrorDetail
)
from services.rate_limiter import RateLimiter
from services.spam_service import SpamDefenseService
from services.geo_service import GeoService
from services.email_service import EmailService
from services.analytics_service import AnalyticsService

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
WIDGET_JS_PATH = STATIC_DIR / "widget.js"

app = FastAPI(
    title="Embeddable Widget & Lead-Capture Platform API",
    description="Multi-tenant, hardened embeddable widget engine with honeypot bot defense, sliding-window rate limiting, and 2-tier geo-fallback chains.",
    version="1.0.0"
)

# Global CORS middleware supporting cross-origin widget embeds and submissions
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service Singletons
rate_limiter = RateLimiter(default_limit=int(os.getenv("RATE_LIMIT_PER_MINUTE", "10")), window_seconds=60)
geo_service = GeoService(timeout_seconds=3.0)
email_service = EmailService()


@app.on_event("startup")
def on_startup():
    init_db()


# ------------------------------------------------------------------------------
# Custom Exception Handlers (HTTP 400, 429)
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
                code="invalid_request",
                message=f"Validation failed on field '{field_name}': {msg}",
                field=field_name,
                details={"validation_errors": errors}
            )
        ).model_dump()
    )


# ------------------------------------------------------------------------------
# Authentication Dependency (Tenant Isolation)
# ------------------------------------------------------------------------------

def get_current_tenant(x_api_key: str = Header(None, alias="X-API-Key"), db: Session = Depends(get_db)) -> Tenant:
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing 'X-API-Key' authentication header."
        )
    tenant = db.query(Tenant).filter(Tenant.api_key == x_api_key).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid 'X-API-Key' header."
        )
    return tenant


# ------------------------------------------------------------------------------
# 1. Fast, Cached Asset & Config Delivery Path
# ------------------------------------------------------------------------------

@app.get("/widget.js", tags=["Delivery"])
def get_widget_script():
    """
    Serves the standalone embeddable JavaScript widget bundle.
    Uses immutable long-term caching header the way a CDN does.
    """
    if not WIDGET_JS_PATH.exists():
        raise HTTPException(status_code=404, detail="widget.js asset not found.")

    return FileResponse(
        WIDGET_JS_PATH,
        media_type="application/javascript",
        headers={
            "Cache-Control": "public, max-age=31536000, immutable",
            "Access-Control-Allow-Origin": "*"
        }
    )


@app.get("/api/v1/widgets/{widget_id}/config", response_model=WidgetPublicConfigResponse, tags=["Delivery"])
def get_widget_public_config(widget_id: str, request: Request, response: Response, db: Session = Depends(get_db)):
    """
    Public endpoint delivering widget rendering configuration.
    Cached for 60 seconds with full cross-origin CORS support.
    """
    widget = db.query(Widget).filter(Widget.id == widget_id).first()
    if not widget:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Widget '{widget_id}' not found.")

    response.headers["Cache-Control"] = "public, max-age=60"
    response.headers["Access-Control-Allow-Origin"] = "*"

    base_url = str(request.base_url).rstrip("/")
    submit_url = f"{base_url}/api/v1/submissions"

    return WidgetPublicConfigResponse(
        widget_id=widget.id,
        title=widget.title,
        description=widget.description,
        button_text=widget.button_text,
        theme_color=widget.theme_color,
        fields_config=widget.fields_config,
        submit_url=submit_url
    )


# ------------------------------------------------------------------------------
# 2. Hardened Public Submission Path (Cross-Origin, Protected)
# ------------------------------------------------------------------------------

@app.post("/api/v1/submissions", response_model=SubmissionResponse, status_code=status.HTTP_201_CREATED, tags=["Submissions"])
def create_submission(
    payload: SubmissionCreateRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Public submission endpoint handling cross-origin requests from customer websites.
    Enforces rate limiting, honeypot spam detection, 2-tier geo fallback, and safe side effects.
    """
    response.headers["Access-Control-Allow-Origin"] = "*"

    # 1. Extract Client IP
    client_ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "127.0.0.1")
    if "," in client_ip:
        client_ip = client_ip.split(",")[0].strip()

    # 2. Sliding Window Rate Limiting (HTTP 429)
    is_allowed, retry_after = rate_limiter.is_allowed(key=f"ip_{client_ip}")
    if not is_allowed:
        response.headers["Retry-After"] = str(retry_after)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Please try again in {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)}
        )

    # 3. Verify Target Widget Exists
    widget = db.query(Widget).filter(Widget.id == payload.widget_id).first()
    if not widget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Target widget '{payload.widget_id}' does not exist."
        )

    # 4. Honeypot Spam Defense Check
    is_spam = SpamDefenseService.is_spam_submission(payload.website_url_hp)

    # 5. 2-Tier Geo-Enrichment Fallback Chain
    country, city, geo_provider = geo_service.enrich_ip(client_ip)

    # 6. Atomic Persistence
    submission = Submission(
        tenant_id=widget.tenant_id,
        widget_id=widget.id,
        name=payload.name,
        email=payload.email,
        message=payload.message,
        ip_address=client_ip,
        country=country,
        city=city,
        geo_provider=geo_provider,
        is_spam=is_spam
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)

    # 7. Safe Side Effect (Email Dispatch — Failure Never Breaks Main Response)
    if not is_spam:
        email_service.send_submission_notification(
            recipient_email="notifications@acme-corp.com",
            widget_title=widget.title,
            submitter_name=payload.name,
            submitter_email=payload.email
        )

    return SubmissionResponse(
        id=submission.id,
        widget_id=submission.widget_id,
        status="flagged_spam" if is_spam else "received",
        message="Thank you! Your submission has been received.",
        country=submission.country,
        city=submission.city,
        geo_enriched=bool(submission.geo_provider),
        created_at=submission.created_at
    )


# ------------------------------------------------------------------------------
# 3. Authenticated Widget Admin CRUD Path
# ------------------------------------------------------------------------------

@app.post("/api/v1/widgets", response_model=WidgetResponse, status_code=status.HTTP_201_CREATED, tags=["Admin Widgets"])
def create_widget(
    payload: WidgetCreateRequest,
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    import uuid
    widget_id = f"w_{uuid.uuid4().hex[:8]}"

    widget = Widget(
        id=widget_id,
        tenant_id=current_tenant.id,
        title=payload.title,
        description=payload.description,
        button_text=payload.button_text,
        theme_color=payload.theme_color,
        allowed_origins=payload.allowed_origins,
        fields_config=[f.model_dump() for f in payload.fields_config] if payload.fields_config else [
            {"name": "name", "type": "text", "label": "Full Name", "required": True},
            {"name": "email", "type": "email", "label": "Email Address", "required": True},
            {"name": "message", "type": "textarea", "label": "Note", "required": False}
        ]
    )
    db.add(widget)
    db.commit()
    db.refresh(widget)
    return widget


@app.get("/api/v1/widgets", response_model=list[WidgetResponse], tags=["Admin Widgets"])
def list_widgets(
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    return db.query(Widget).filter(Widget.tenant_id == current_tenant.id).all()


@app.get("/api/v1/widgets/{widget_id}", response_model=WidgetResponse, tags=["Admin Widgets"])
def get_widget(
    widget_id: str,
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    widget = db.query(Widget).filter(Widget.id == widget_id, Widget.tenant_id == current_tenant.id).first()
    if not widget:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Widget not found.")
    return widget


@app.delete("/api/v1/widgets/{widget_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Admin Widgets"])
def delete_widget(
    widget_id: str,
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    widget = db.query(Widget).filter(Widget.id == widget_id, Widget.tenant_id == current_tenant.id).first()
    if not widget:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Widget not found.")
    db.delete(widget)
    db.commit()
    return None


# ------------------------------------------------------------------------------
# 4. Authenticated Owner Analytics Dashboard Path
# ------------------------------------------------------------------------------

@app.get("/api/v1/analytics/stats", response_model=AnalyticsStatsResponse, tags=["Admin Analytics"])
def get_analytics_stats(
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    stats = AnalyticsService.get_tenant_stats(db, current_tenant.id)
    return AnalyticsStatsResponse(**stats)


@app.get("/api/v1/analytics/geo", response_model=GeoAnalyticsResponse, tags=["Admin Analytics"])
def get_geo_analytics(
    current_tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    geo_data = AnalyticsService.get_geo_breakdown(db, current_tenant.id)
    return GeoAnalyticsResponse(**geo_data)


# ------------------------------------------------------------------------------
# Health Check
# ------------------------------------------------------------------------------

@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": "Embeddable Widget & Lead-Capture Platform",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
