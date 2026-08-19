# BUILDLOG.md — AI Build Transparency Log

This document records key architectural decisions, design tradeoffs, AI-assisted work, and human overrides throughout the development of the **AI Image Understanding & Content Matching Engine Capstone**.

---

## Phase 1: Design & Architecture Setup (Date: 2026-08-19)

### Key Architectural Decisions:
1. **The Production Mismatch Guard Principle:**
   - In production AI, avoiding an incorrect recommendation is more critical than finding an approximate match. We designed a multi-criteria safety guard combining:
     - G1: Cosine similarity threshold >= 0.72.
     - G2: Model confidence >= 0.75.
     - G3: Subject/Entity alignment check (e.g. Article: "Red Fox" vs Image: "Gray Wolf" ➔ Refused).
2. **Deterministic & Cloud-Agnostic Embeddings:**
   - Supports Gemini/OpenRouter embedding models and a deterministic local embedding engine for 100% offline, reproducible testing.
3. **Structured Vision Ingestion:**
   - Ingests image corpus with strict Pydantic v2 validation (`subject`, `category`, `attributes`, `caption`, `confidence`).
   - Automatically quarantines responses with confidence < 0.70.
4. **Per-Call Micro-Cents Cost Tracking:**
   - Logs token usage, execution time, and integer micro-cents to `cost_logs` table.
