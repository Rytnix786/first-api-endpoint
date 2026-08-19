# test_image_matching.py — Automated Pytest Suite Verifying All Image Matching Capstone Probes

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import app
from database import get_db
from models import Base, ImageItem, BlogPost, ReviewLog, CostLog
from schemas import ImageTagSchema
from services.mismatch_guard import MismatchGuard
from services.embedding_service import EmbeddingService

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
    """Sets up fresh in-memory SQLite schema and seed records for each test."""
    Base.metadata.drop_all(bind=engine_test)
    Base.metadata.create_all(bind=engine_test)

    db = TestingSessionLocal()
    # Seed sample images
    img_fox = ImageItem(
        id="img_fox_01",
        filename="red_fox.jpg",
        subject="red fox",
        category="animal",
        attributes=["orange fur", "forest", "wild"],
        caption="A red fox in autumn forest",
        confidence=0.94,
        embedding=EmbeddingService.get_embedding("red fox animal orange fur forest wild A red fox in autumn forest"),
        status="processed"
    )
    img_wolf = ImageItem(
        id="img_wolf_01",
        filename="gray_wolf.jpg",
        subject="gray wolf",
        category="animal",
        attributes=["gray fur", "snow", "pack"],
        caption="A gray wolf in snowy timberland",
        confidence=0.95,
        embedding=EmbeddingService.get_embedding("gray wolf animal gray fur snow pack A gray wolf in snowy timberland"),
        status="processed"
    )
    img_dog = ImageItem(
        id="img_dog_01",
        filename="golden_retriever.jpg",
        subject="dog",
        category="animal",
        attributes=["golden retriever", "pet", "park"],
        caption="A golden retriever dog in a park",
        confidence=0.96,
        embedding=EmbeddingService.get_embedding("dog animal golden retriever pet park A golden retriever dog in a park"),
        status="processed"
    )
    img_blurry = ImageItem(
        id="img_blurry_01",
        filename="blurry.jpg",
        subject="unknown",
        category="other",
        attributes=["blurry"],
        caption="A blurry shadow",
        confidence=0.45,
        embedding=EmbeddingService.get_embedding("unknown other blurry A blurry shadow"),
        status="flagged_low_confidence"
    )

    # Seed sample posts
    post_fox = BlogPost(
        id="p_fox_01",
        title="Behavior of the Red Fox",
        content="The red fox (Vulpes vulpes) lives in woodlands and autumn forests.",
        target_subject="red fox",
        embedding=EmbeddingService.get_embedding("Behavior of the Red Fox The red fox (Vulpes vulpes) lives in woodlands and autumn forests. red fox")
    )
    post_cooking = BlogPost(
        id="p_cooking_01",
        title="Italian Pizza Recipe",
        content="Making fresh pizza dough with flour and tomatoes.",
        target_subject="culinary recipe",
        embedding=EmbeddingService.get_embedding("Italian Pizza Recipe Making fresh pizza dough with flour and tomatoes. culinary recipe")
    )

    db.add_all([img_fox, img_wolf, img_dog, img_blurry, post_fox, post_cooking])
    db.commit()
    db.close()
    yield


# ------------------------------------------------------------------------------
# PROBE 1: Structured Vision Schema Validation
# ------------------------------------------------------------------------------

def test_probe_1_structured_vision_schema_validation():
    """Verify vision output validates against ImageTagSchema."""
    valid_data = {
        "subject": "red fox",
        "category": "animal",
        "attributes": ["orange fur", "wild"],
        "caption": "A red fox in the snow",
        "confidence": 0.92
    }
    schema_instance = ImageTagSchema(**valid_data)
    assert schema_instance.subject == "red fox"
    assert schema_instance.confidence == 0.92

    # Malformed data should fail validation
    with pytest.raises(Exception):
        ImageTagSchema(subject="x", category="animal", caption="too short", confidence=1.5)


# ------------------------------------------------------------------------------
# PROBE 2: Low-Confidence Image Flagging
# ------------------------------------------------------------------------------

def test_probe_2_low_confidence_flagging():
    """Verify images with confidence < 0.70 are flagged."""
    res = client.get("/api/v1/images")
    assert res.status_code == 200
    images = res.json()
    blurry = next(i for i in images if i["id"] == "img_blurry_01")
    assert blurry["status"] == "flagged_low_confidence"
    assert blurry["confidence"] < 0.70


# ------------------------------------------------------------------------------
# PROBE 3: Semantic Vector Matching & Ranking
# ------------------------------------------------------------------------------

def test_probe_3_semantic_matching_and_ranking():
    """Verify red fox article ranks red fox image as top candidate."""
    res = client.get("/api/v1/posts/p_fox_01/matches")
    assert res.status_code == 200
    data = res.json()
    assert data["has_confident_match"] is True
    top_candidate = data["candidates"][0]
    assert top_candidate["image_id"] == "img_fox_01"
    assert top_candidate["guard_verdict"] == "ACCEPTED"


# ------------------------------------------------------------------------------
# PROBE 4: Mismatch Guard Refusal (Fox vs. Wolf Refusal)
# ------------------------------------------------------------------------------

def test_probe_4_mismatch_guard_refuses_wolf_on_fox():
    """Verify the signature test: wolf image is refused on fox article with reason."""
    guard = MismatchGuard()
    passed, verdict, reason = guard.evaluate_candidate(
        post_target_subject="red fox",
        post_title="Behavior of the Red Fox",
        image_subject="gray wolf",
        image_category="animal",
        image_caption="A gray wolf in snowy timberland",
        similarity_score=0.76,
        model_confidence=0.95
    )
    assert passed is False
    assert verdict == "REFUSED"
    assert "Subject mismatch" in reason
    assert "red fox" in reason and "gray wolf" in reason


# ------------------------------------------------------------------------------
# PROBE 5: Gating & Safe Rejection (No Confident Match)
# ------------------------------------------------------------------------------

def test_probe_5_no_confident_match_below_threshold():
    """Verify cooking article with no matching image returns no confident match."""
    res = client.get("/api/v1/posts/p_cooking_01/matches")
    assert res.status_code == 200
    data = res.json()
    assert data["has_confident_match"] is False
    assert "No confident match" in data["status_summary"]


# ------------------------------------------------------------------------------
# PROBE 6: Editorial Review Workflow (Approve / Reject)
# ------------------------------------------------------------------------------

def test_probe_6_review_workflow_approval_and_rejection():
    """Verify approve and reject endpoints persist decisions to audit trail."""
    # Test Approve
    res_app = client.post("/api/v1/reviews/approve", json={
        "post_id": "p_fox_01",
        "image_id": "img_fox_01",
        "reason": "Perfect match for hero banner"
    })
    assert res_app.status_code == 201
    assert res_app.json()["decision"] == "approved"

    # Test Reject
    res_rej = client.post("/api/v1/reviews/reject", json={
        "post_id": "p_fox_01",
        "image_id": "img_wolf_01",
        "reason": "Wolf image is inappropriate for fox article"
    })
    assert res_rej.status_code == 201
    assert res_rej.json()["decision"] == "rejected"


# ------------------------------------------------------------------------------
# PROBE 7: Cost Telemetry Endpoint
# ------------------------------------------------------------------------------

def test_probe_7_cost_tracking_telemetry():
    """Verify cost telemetry logs are tracked and retrievable."""
    db = TestingSessionLocal()
    cost = CostLog(
        operation="vision_tagging",
        model_id="google/gemini-2.0-flash-exp:free",
        input_tokens=150,
        output_tokens=60,
        cost_micro_cents=58,
        duration_ms=450
    )
    db.add(cost)
    db.commit()
    db.close()

    res = client.get("/api/v1/costs")
    assert res.status_code == 200
    costs = res.json()
    assert len(costs) >= 1
    assert costs[0]["cost_micro_cents"] == 58
