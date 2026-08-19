# test_widget_platform.py — Automated Test Suite Verifying Probes 1 to 6

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import patch

from app import app, rate_limiter, geo_service, email_service
from database import get_db
from models import Base, Tenant, Widget, Submission

# Use StaticPool in-memory SQLite for deterministic, isolated testing
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

engine_test = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_test_db():
    """Recreates clean database schema and test seeds for every test function."""
    Base.metadata.drop_all(bind=engine_test)
    Base.metadata.create_all(bind=engine_test)
    rate_limiter.reset()
    geo_service.provider_a_enabled = True
    geo_service.provider_b_enabled = True
    email_service.simulate_failure = False

    db = TestingSessionLocal()
    tenant_1 = Tenant(id="tenant_acme", name="Acme Corp", api_key="ak_acme_123")
    tenant_2 = Tenant(id="tenant_beta", name="Beta Inc", api_key="ak_beta_456")
    widget_1 = Widget(id="w_demo_123", tenant_id="tenant_acme", title="Acme Newsletter")
    widget_2 = Widget(id="w_beta_789", tenant_id="tenant_beta", title="Beta Survey")
    db.add_all([tenant_1, tenant_2, widget_1, widget_2])
    db.commit()
    db.close()
    yield


# ------------------------------------------------------------------------------
# PROBE 1: Cross-Origin CORS & Preflight
# ------------------------------------------------------------------------------

def test_probe_1_cors_headers_and_preflight():
    """Verify CORS headers and OPTIONS preflight allow cross-origin requests."""
    # Test widget.js CORS
    res_script = client.get("/widget.js")
    assert res_script.status_code == 200
    assert "access-control-allow-origin" in res_script.headers

    # Test widget config CORS
    res_config = client.get("/api/v1/widgets/w_demo_123/config")
    assert res_config.status_code == 200
    assert "public, max-age=60" in res_config.headers.get("cache-control", "")
    assert res_config.headers.get("access-control-allow-origin") == "*"

    # Test OPTIONS preflight for submissions
    res_options = client.options(
        "/api/v1/submissions",
        headers={
            "Origin": "http://customer-site.com",
            "Access-Control-Request-Method": "POST"
        }
    )
    assert res_options.status_code == 200
    assert res_options.headers.get("access-control-allow-origin") == "*"


# ------------------------------------------------------------------------------
# PROBE 2: Boundary Input Validation (HTTP 400, 404)
# ------------------------------------------------------------------------------

def test_probe_2_input_validation_and_status_honesty():
    """Verify malformed input returns HTTP 400 and invalid widget returns HTTP 404."""
    # Invalid email
    res_bad_email = client.post("/api/v1/submissions", json={
        "widget_id": "w_demo_123",
        "name": "Jane",
        "email": "not-a-valid-email",
        "message": "Hello"
    })
    assert res_bad_email.status_code == 400
    assert res_bad_email.json()["error"]["field"] == "email"

    # Non-existent widget ID
    res_not_found = client.post("/api/v1/submissions", json={
        "widget_id": "w_non_existent",
        "name": "Jane",
        "email": "jane@example.com",
        "message": "Hello"
    })
    assert res_not_found.status_code == 404


# ------------------------------------------------------------------------------
# PROBE 3: Honeypot Spam Defense
# ------------------------------------------------------------------------------

def test_probe_3_honeypot_spam_defense():
    """Verify filled honeypot field is flagged as spam without failing the request."""
    res_spam = client.post("/api/v1/submissions", json={
        "widget_id": "w_demo_123",
        "name": "Bot User",
        "email": "bot@spammer.xyz",
        "message": "Buy cheap stuff",
        "_website_url_hp": "http://spambot-link.com"  # Bot filled hidden field
    })
    assert res_spam.status_code == 201
    data = res_spam.json()
    assert data["status"] == "flagged_spam"

    # Verify marked is_spam in DB
    db = TestingSessionLocal()
    sub = db.query(Submission).filter(Submission.id == data["id"]).first()
    assert sub.is_spam is True
    db.close()


# ------------------------------------------------------------------------------
# PROBE 4: Sliding-Window Rate Limiting (HTTP 429)
# ------------------------------------------------------------------------------

def test_probe_4_rate_limiting_burst():
    """Verify burst of requests exceeding limit returns HTTP 429 with Retry-After header."""
    headers = {"X-Forwarded-For": "203.0.113.195"}

    # Default limit is 10 requests per minute
    for i in range(10):
        res = client.post("/api/v1/submissions", json={
            "widget_id": "w_demo_123",
            "name": f"User {i}",
            "email": f"user{i}@example.com",
            "message": "Test"
        }, headers=headers)
        assert res.status_code == 201

    # 11th request exceeds limit -> 429 Too Many Requests
    res_blocked = client.post("/api/v1/submissions", json={
        "widget_id": "w_demo_123",
        "name": "Burst User",
        "email": "burst@example.com",
        "message": "Burst"
    }, headers=headers)
    assert res_blocked.status_code == 429
    assert "retry-after" in res_blocked.headers
    assert int(res_blocked.headers["retry-after"]) >= 1


# ------------------------------------------------------------------------------
# PROBE 5: 2-Tier Geo Fallback Chain & Graceful Degradation
# ------------------------------------------------------------------------------

def test_probe_5_geo_fallback_chain():
    """Verify fallback from Provider A -> Provider B -> Graceful null degrade."""
    headers = {"X-Forwarded-For": "8.8.8.8"}

    # 1. Provider A Active
    with patch.object(geo_service, "enrich_ip", return_value=("United States", "Ashburn", "ip-api.com")):
        res_a = client.post("/api/v1/submissions", json={
            "widget_id": "w_demo_123",
            "name": "Alice",
            "email": "alice@example.com"
        }, headers=headers)
        assert res_a.status_code == 201
        assert res_a.json()["country"] == "United States"

    # 2. Provider A Down -> Provider B takes over
    with patch.object(geo_service, "enrich_ip", return_value=("United States", "Chicago", "ipapi.co")):
        res_b = client.post("/api/v1/submissions", json={
            "widget_id": "w_demo_123",
            "name": "Bob",
            "email": "bob@example.com"
        }, headers=headers)
        assert res_b.status_code == 201
        assert res_b.json()["country"] == "United States"

    # 3. Both Providers Down -> Degrade gracefully without geo (HTTP 201)
    with patch.object(geo_service, "enrich_ip", return_value=(None, None, None)):
        res_none = client.post("/api/v1/submissions", json={
            "widget_id": "w_demo_123",
            "name": "Charlie",
            "email": "charlie@example.com"
        }, headers=headers)
        assert res_none.status_code == 201
        assert res_none.json()["country"] is None
        assert res_none.json()["geo_enriched"] is False


# ------------------------------------------------------------------------------
# PROBE 6: Safe Side Effects (Email Failure Resilience)
# ------------------------------------------------------------------------------

def test_probe_6_email_side_effect_failure_does_not_break_submission():
    """Verify that simulated email server failure does not prevent HTTP 201 submission success."""
    email_service.simulate_failure = True

    res = client.post("/api/v1/submissions", json={
        "widget_id": "w_demo_123",
        "name": "David",
        "email": "david@example.com",
        "message": "Email outage test"
    })

    assert res.status_code == 201
    data = res.json()
    assert data["message"] == "Thank you! Your submission has been received."

    # Verify saved in database
    db = TestingSessionLocal()
    saved_sub = db.query(Submission).filter(Submission.id == data["id"]).first()
    assert saved_sub is not None
    assert saved_sub.name == "David"
    db.close()


# ------------------------------------------------------------------------------
# PROBE 7: Multi-Tenant Admin CRUD & Isolation
# ------------------------------------------------------------------------------

def test_probe_7_tenant_isolation_and_admin_crud():
    """Verify tenant isolation: Tenant A cannot view or delete Tenant B widgets."""
    # Tenant 1 lists own widgets
    res_list = client.get("/api/v1/widgets", headers={"X-API-Key": "ak_acme_123"})
    assert res_list.status_code == 200
    widgets = res_list.json()
    assert len(widgets) == 1
    assert widgets[0]["id"] == "w_demo_123"

    # Tenant 1 attempts to access Tenant 2 widget -> 404
    res_unauth = client.get("/api/v1/widgets/w_beta_789", headers={"X-API-Key": "ak_acme_123"})
    assert res_unauth.status_code == 404

    # Create new widget for Tenant 1
    res_create = client.post("/api/v1/widgets", headers={"X-API-Key": "ak_acme_123"}, json={
        "title": "Beta Signup",
        "description": "Join our beta testing cohort.",
        "button_text": "Sign Up"
    })
    assert res_create.status_code == 201
    assert res_create.json()["title"] == "Beta Signup"


# ------------------------------------------------------------------------------
# PROBE 8: Analytics Dashboard
# ------------------------------------------------------------------------------

def test_probe_8_analytics_dashboard():
    """Verify analytics endpoints calculate counts, submissions, and geo breakdown."""
    db = TestingSessionLocal()
    sub1 = Submission(tenant_id="tenant_acme", widget_id="w_demo_123", name="U1", email="u1@e.com", ip_address="1.1.1.1", country="USA", city="New York")
    sub2 = Submission(tenant_id="tenant_acme", widget_id="w_demo_123", name="U2", email="u2@e.com", ip_address="1.1.1.2", country="UK", city="London")
    sub3 = Submission(tenant_id="tenant_acme", widget_id="w_demo_123", name="Spam", email="spam@e.com", ip_address="1.1.1.3", is_spam=True)
    db.add_all([sub1, sub2, sub3])
    db.commit()
    db.close()

    res_stats = client.get("/api/v1/analytics/stats", headers={"X-API-Key": "ak_acme_123"})
    assert res_stats.status_code == 200
    stats = res_stats.json()
    assert stats["total_submissions"] == 2
    assert stats["spam_blocked_count"] == 1

    res_geo = client.get("/api/v1/analytics/geo", headers={"X-API-Key": "ak_acme_123"})
    assert res_geo.status_code == 200
    geo = res_geo.json()
    assert "USA" in geo["country_breakdown"]
    assert "UK" in geo["country_breakdown"]
