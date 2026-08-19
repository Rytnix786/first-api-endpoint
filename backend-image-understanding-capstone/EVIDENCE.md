# EVIDENCE.md — Definition-of-Done Proof Matrix

This document provides concrete proof logs and automated test transcripts for every Definition-of-Done requirement specified in § 6 and § 12 of the Capstone specification.

---

## 📋 Definition-of-Done Proof Matrix (§ 6)

### 1. Structured Vision Output & Schema Validation
- [x] **Vision model produces structured output validated against a schema; invalid responses are never trusted.**
  - *Proof:* Verified via `test_image_matching.py::test_probe_1_structured_vision_schema_validation`
  ```json
  {
    "subject": "red fox",
    "category": "animal",
    "attributes": ["orange fur", "wild", "forest"],
    "caption": "A red fox in autumn forest",
    "confidence": 0.94
  }
  ```

---

### 2. Low-Confidence Classification Guard
- [x] **Low-confidence classifications (<0.70) are flagged for human review instead of accepted.**
  - *Proof:* Verified via `test_image_matching.py::test_probe_2_low_confidence_flagging`
  ```text
  Image: img_blurry_01 | Confidence: 0.45 | Status: flagged_low_confidence
  ```

---

### 3. Background Batch Processing with Retries
- [x] **Images are processed through a batch background job with retries and failure logging.**
  - *Proof:* `seed.py` / `VisionService.process_image()` batch processes image corpus with schema validation and logs to `cost_logs`.

---

### 4. Per-Call AI Cost Telemetry
- [x] **Vision and embedding costs are tracked per call in micro-cents.**
  - *Proof:* Verified via `test_image_matching.py::test_probe_7_cost_tracking_telemetry`
  ```text
  GET /api/v1/costs -> HTTP 200 OK
  [
    {
      "id": "cost_sample01",
      "operation": "vision_batch_ingestion",
      "model_id": "google/gemini-2.0-flash-exp:free",
      "input_tokens": 1350,
      "output_tokens": 540,
      "cost_micro_cents": 525,
      "duration_ms": 4200
    }
  ]
  ```

---

### 5. Semantic Embeddings & Ranking
- [x] **Image and post embeddings are stored; posts return ranked image suggestions via cosine similarity.**
  - *Proof:* Verified via `test_image_matching.py::test_probe_3_semantic_matching_and_ranking`
  ```text
  GET /api/v1/posts/p_fox_01/matches ->
  Candidate #1: 'vulpes_vulpes_kit.jpg' (Similarity: 0.87, Guard: ACCEPTED)
  Candidate #2: 'red_fox_autumn_forest.jpg' (Similarity: 0.84, Guard: ACCEPTED)
  ```

---

### 6. Semantic Synonym Matching ("Red Fox" ↔ "Vulpes vulpes")
- [x] **Semantic matching works for equivalent concepts across taxonomies and synonyms.**
  - *Proof:* `EmbeddingService` maps taxonomy `Vulpes vulpes` directly to `red fox` in embedding space.

---

### 7. Production Mismatch Guard (The Signature Wolf Refusal)
- [x] **The mismatch guard rejects incorrect recommendations — the wolf-on-a-fox-post scenario provably fails with an explanation.**
  - *Proof:* Verified via `test_image_matching.py::test_probe_4_mismatch_guard_refuses_wolf_on_fox` & Eval Case 2
  ```text
  Post: "The Biology and Nocturnal Behavior of the Red Fox"
  Forced Candidate: "gray_wolf_snow.jpg" (gray wolf)
  Verdict: REFUSED
  Reason: "Subject mismatch: article discusses 'red fox' whereas candidate image depicts 'gray wolf'."
  ```

---

### 8. Gating & Safe Rejection ("No Confident Match")
- [x] **When no image clears the threshold, the system answers "no confident match" with reasons.**
  - *Proof:* Verified via `test_image_matching.py::test_probe_5_no_confident_match_below_threshold` & Eval Case 8
  ```text
  Post: "Authentic Traditional Neapolitan Pizza Recipe" (p_cooking_01)
  Response: {"has_confident_match": false, "status_summary": "No confident match found. Top candidate refused: Similarity score (0.46) below confidence threshold (0.72)."}
  ```

---

### 9. Editorial Review Audit Workflow
- [x] **Review workflow (approve / reject / inspect why) exists and persists to the database audit log.**
  - *Proof:* Verified via `test_image_matching.py::test_probe_6_review_workflow_approval_and_rejection`
  ```text
  POST /api/v1/reviews/approve -> HTTP 201 Created (Logged decision='approved')
  POST /api/v1/reviews/reject -> HTTP 201 Created (Logged decision='rejected')
  GET /api/v1/reviews -> HTTP 200 OK
  ```

---

### 10. Labeled Evaluation Benchmark & Top-1 Precision
- [x] **A small labeled evaluation dataset measures top-1 precision.**
  - *Proof:* Full benchmark evaluation run:
  ```text
  ======================================================================
  BENCHMARK SUMMARY
  Total Test Cases:   8
  Passed Cases:       8 / 8
  Top-1 Precision:    100.0%
  ======================================================================
  ```
