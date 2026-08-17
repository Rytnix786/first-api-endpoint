# app.py — FastAPI LLM Enrichment Microservice

import os
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from schemas import EnrichRequest, APIResponseEnvelope, ErrorEnvelope, ErrorDetail
from llm_client import (
    LLMClient,
    SchemaValidationException,
    LLMTimeoutException,
    LLMAuthenticationException
)

app = FastAPI(
    title="Task7-w7-a1 Content Enrichment LLM Microservice",
    description="Resilient, schema-validated LLM API endpoint featuring 1-shot repair retries, quarantine logging, and cost tracking.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

llm_client = LLMClient()


# ------------------------------------------------------------------------------
# Custom Exception Handlers (HTTP 400, 422, 504)
# ------------------------------------------------------------------------------

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Stage 1: Reject garbage inputs before calling the model (HTTP 400)."""
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
                message=f"Input validation failed on field '{field_name}': {msg}",
                field=field_name,
                details={"validation_errors": errors}
            )
        ).model_dump()
    )


@app.exception_handler(SchemaValidationException)
async def schema_validation_exception_handler(request: Request, exc: SchemaValidationException):
    """Stage 3: Return 422 Unprocessable Entity when model output fails schema after repair retry."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorEnvelope(
            error=ErrorDetail(
                code="schema_validation_failed",
                message="Model failed to produce valid JSON matching the schema after repair retry.",
                details={
                    "raw_output": exc.raw_output,
                    "error_details": exc.error_details
                }
            )
        ).model_dump()
    )


@app.exception_handler(LLMTimeoutException)
async def llm_timeout_exception_handler(request: Request, exc: LLMTimeoutException):
    """Stage 4: Return 504 Gateway Timeout when LLM call or retries time out."""
    return JSONResponse(
        status_code=status.HTTP_504_GATEWAY_TIMEOUT,
        content=ErrorEnvelope(
            error=ErrorDetail(
                code="llm_timeout",
                message=str(exc)
            )
        ).model_dump()
    )


@app.exception_handler(LLMAuthenticationException)
async def llm_auth_exception_handler(request: Request, exc: LLMAuthenticationException):
    """Stage 4: Return 401 Unauthorized when API Key is invalid (Fast Failure)."""
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content=ErrorEnvelope(
            error=ErrorDetail(
                code="authentication_error",
                message=str(exc)
            )
        ).model_dump()
    )


# ------------------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------------------

@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "llm_stub_mode": os.getenv("LLM_STUB", "0") in ("1", "true", "yes"),
        "llm_enabled": os.getenv("LLM_ENABLED", "true") in ("1", "true", "yes"),
        "model_id": os.getenv("OPENROUTER_MODEL_ID", "openrouter/free")
    }


@app.post("/api/v1/enrich", response_model=APIResponseEnvelope, tags=["Enrichment"])
def enrich_content(payload: EnrichRequest):
    """
    Enriches unstructured technical text into validated JSON metadata.
    Enforces input validation (HTTP 400), 1-shot repair retries (HTTP 422), timeouts (HTTP 504), and kill switch.
    """
    enriched_data, meta = llm_client.enrich_content(input_text=payload.text)
    
    return APIResponseEnvelope(
        status="success",
        data=enriched_data,
        meta=meta
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
