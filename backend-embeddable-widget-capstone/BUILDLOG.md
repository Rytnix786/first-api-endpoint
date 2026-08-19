# BUILDLOG.md — AI Build Transparency Log

This document records key architectural decisions, design tradeoffs, AI-assisted work, and human overrides throughout the development of the **Embeddable Widget & Lead-Capture Platform Capstone**.

---

## Phase 1: Design & Architecture Setup (Date: 2026-08-19)

### Key Architectural Decisions:
1. **Three-Path Request Separation:**
   - Isolated the system into three distinct operational pathways: Authenticated Admin CRUD, Public Cached Asset Delivery, and Public Hardened Cross-Origin Submissions.
2. **Resilience Principle (Degrade, Never Fail):**
   - Geo-enrichment is implemented as a 2-tier fallback chain (`ip-api.com` ➔ `ipapi.co` ➔ graceful no-geo degrade). Upstream outages will never drop a legitimate customer lead.
   - Side effects (email/webhook notification) are wrapped in try/except boundaries so secondary infrastructure hiccups do not block the primary HTTP 201 response.
3. **Honeypot Bot Defense:**
   - Adopted a hidden `_website_url_hp` form field approach. Bots that auto-fill hidden fields are immediately flagged and dropped without alert.
4. **Sliding-Window Rate Limiting:**
   - Implemented an IP-keyed sliding window rate limiter that returns honest HTTP 429 status codes with `Retry-After` headers.
