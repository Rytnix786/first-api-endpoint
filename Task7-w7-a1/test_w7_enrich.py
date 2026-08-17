# test_w7_enrich.py — Automated Test Suite for Week 7 (W7 - A17) Task7-w7-a1

import json
import os
import pytest
from fastapi.testclient import TestClient
from pathlib import Path
from unittest.mock import patch, MagicMock

from app import app
from llm_client import (
    LLMClient,
    SchemaValidationException,
    LLMTimeoutException,
    LLMAuthenticationException
)
from schemas import CategoryEnum, DepthEnum, FlagEnum

client = TestClient(app)
BASE_DIR = Path(__file__).resolve().parent
LOGS_DIR = BASE_DIR / "logs"
QUARANTINE_FILE = LOGS_DIR / "quarantine.jsonl"


# ------------------------------------------------------------------------------
# Stage 1: Input Validation (HTTP 400) & Stub Mode (LLM_STUB=1)
# ------------------------------------------------------------------------------

def test_stage1_input_validation_400_too_short():
    """Verify invalid input (<10 chars) returns HTTP 400 before model call."""
    response = client.post("/api/v1/enrich", json={"text": "short"})
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "invalid_request"
    assert data["error"]["field"] == "text"


def test_stage1_stub_mode_success(monkeypatch):
    """Verify LLM_STUB=1 returns schema-valid response with 0 cost."""
    monkeypatch.setenv("LLM_STUB", "1")
    response = client.post("/api/v1/enrich", json={
        "text": "We migrated our PostgreSQL database cluster to Kubernetes using Zalando operator."
    })
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["meta"]["stub_mode"] is True
    assert payload["meta"]["cost_micro_cents"] == 0
    assert payload["data"]["category"] == "engineering"


# ------------------------------------------------------------------------------
# Stage 2: Versioned System Prompt Loading
# ------------------------------------------------------------------------------

def test_stage2_prompt_version_loading():
    """Verify prompts/v1.txt system prompt loads correctly."""
    llm = LLMClient()
    prompt = llm.load_system_prompt("v1")
    assert "You are an expert technical content analyst API engine." in prompt
    assert "Output JSON Schema Specification" in prompt
    assert "Few-Shot Examples" in prompt


# ------------------------------------------------------------------------------
# Stage 3: Schema Parsing, 1-Shot Repair Retry & Quarantine Logging (HTTP 422)
# ------------------------------------------------------------------------------

def test_stage3_repair_retry_success(monkeypatch):
    """Verify 1-shot repair retry fixes malformed Attempt 1 output."""
    monkeypatch.setenv("LLM_STUB", "0")
    monkeypatch.setenv("LLM_ENABLED", "true")

    valid_json = json.dumps({
        "category": "devops_cloud",
        "summary": "Migrated database to Kubernetes with WAL archiving.",
        "technical_depth": "advanced",
        "quality_flags": ["contains_code"],
        "confidence": 0.95,
        "reason": "Infrastructure migration details."
    })

    # Mock _call_api_with_retry: Attempt 1 returns broken JSON, Attempt 2 returns valid JSON
    with patch.object(LLMClient, "_call_api_with_retry") as mock_api:
        mock_api.side_effect = [
            ("BROKEN NON-JSON TEXT", 100, 50),
            (valid_json, 150, 60)
        ]
        
        response = client.post("/api/v1/enrich", json={
            "text": "We migrated our PostgreSQL database cluster to Kubernetes using Zalando operator."
        })

        assert response.status_code == 200
        payload = response.json()
        assert payload["meta"]["repair_count"] == 1
        assert payload["data"]["category"] == "devops_cloud"


def test_stage3_quarantine_logging_422(monkeypatch):
    """Verify failure after repair retry returns HTTP 422 and logs to quarantine.jsonl."""
    monkeypatch.setenv("LLM_STUB", "0")
    monkeypatch.setenv("LLM_ENABLED", "true")

    # Clear quarantine file if exists
    if QUARANTINE_FILE.exists():
        QUARANTINE_FILE.unlink()

    with patch.object(LLMClient, "_call_api_with_retry") as mock_api:
        mock_api.side_effect = [
            ("INVALID JSON 1", 100, 50),
            ("INVALID JSON 2", 150, 60)
        ]

        response = client.post("/api/v1/enrich", json={
            "text": "We migrated our PostgreSQL database cluster to Kubernetes using Zalando operator."
        })

        assert response.status_code == 422
        data = response.json()
        assert data["error"]["code"] == "schema_validation_failed"
        
        # Verify quarantine.jsonl entry exists
        assert QUARANTINE_FILE.exists()
        lines = QUARANTINE_FILE.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) >= 1
        last_entry = json.loads(lines[-1])
        assert last_entry["raw_output"] == "INVALID JSON 2"


# ------------------------------------------------------------------------------
# Stage 4: Kill Switch (LLM_ENABLED=false), Timeout (HTTP 504), Auth Fast Fail (HTTP 401)
# ------------------------------------------------------------------------------

def test_stage4_kill_switch_active(monkeypatch):
    """Verify LLM_ENABLED=false returns deterministic fallback without calling model."""
    monkeypatch.setenv("LLM_ENABLED", "false")
    monkeypatch.setenv("LLM_STUB", "0")

    response = client.post("/api/v1/enrich", json={
        "text": "We migrated our PostgreSQL database cluster to Kubernetes using Zalando operator."
    })
    assert response.status_code == 200
    payload = response.json()
    assert payload["meta"]["kill_switch_active"] is True
    assert payload["data"]["category"] == "other"
    assert "needs_review" in payload["data"]["quality_flags"]


def test_stage4_timeout_504():
    """Verify LLM timeout raises HTTP 504 Gateway Timeout."""
    with patch.object(LLMClient, "enrich_content", side_effect=LLMTimeoutException("LLM API call timed out")):
        response = client.post("/api/v1/enrich", json={
            "text": "We migrated our PostgreSQL database cluster to Kubernetes using Zalando operator."
        })
        assert response.status_code == 504
        data = response.json()
        assert data["error"]["code"] == "llm_timeout"


def test_stage4_auth_failure_401_no_retries():
    """Verify HTTP 401 invalid API key fails fast immediately with HTTP 401."""
    with patch.object(LLMClient, "enrich_content", side_effect=LLMAuthenticationException("Invalid API Key")):
        response = client.post("/api/v1/enrich", json={
            "text": "We migrated our PostgreSQL database cluster to Kubernetes using Zalando operator."
        })
        assert response.status_code == 401
        data = response.json()
        assert data["error"]["code"] == "authentication_error"


# ------------------------------------------------------------------------------
# Stage 5: Health Check & General API Verification
# ------------------------------------------------------------------------------

def test_health_check():
    """Verify /health endpoint returns system configuration."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "model_id" in data
