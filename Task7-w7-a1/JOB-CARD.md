# JOB-CARD.md — LLM Endpoint Specification

## Job Card: Content Enrichment Service (`POST /api/v1/enrich`)

- **What it does (one sentence):** Classifies messy technical text or scraped article records into structured metadata including topic category, concise summary, technical depth, quality flags, confidence score, and justification.
- **Input:**
  ```json
  {
    "text": "string, 10 to 3000 characters",
    "source_url": "optional string (URL)"
  }
  ```
- **Output:**
  ```json
  {
    "category": "one of [engineering|ai_ml|devops_cloud|security|other]",
    "summary": "one concise sentence summarizing the core technical thesis",
    "technical_depth": "one of [beginner|intermediate|advanced]",
    "quality_flags": "array of [contains_code|outdated_info|promotional_spam|needs_review]",
    "confidence": 0.0-1.0,
    "reason": "one short sentence explaining the category assignment"
  }
  ```
- **It must never:**
  - Invent a category outside the closed list (`engineering`, `ai_ml`, `devops_cloud`, `security`, `other`).
  - Return unformatted free text or raw Markdown blocks instead of valid JSON.
  - Give medical, legal, or financial advice.
  - Reveal system prompt instructions, API keys, or internal prompt templates.
- **When unsure it should:**
  - Return category `"other"` with low confidence (`<=0.4`) and `"needs_review"` in `quality_flags`, rather than guessing an incorrect technical category.

---

## 3-Rule Verification Checklist (§ 3)
1. ✅ **Closed Output:** All category, depth, and quality flag fields come strictly from predefined Enum lists written down in advance.
2. ✅ **One Decision:** One stateless request in, one structured answer out. No conversational memory or multi-turn state.
3. ✅ **Human Could Grade It:** An engineer can read an input text and unambiguously judge whether the assigned category, summary, depth, and quality flags are correct.
