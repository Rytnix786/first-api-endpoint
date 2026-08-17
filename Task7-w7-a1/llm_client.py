# llm_client.py — Resilience-Focused OpenRouter LLM Client with Repair Retry & Quarantine Logging

import json
import logging
import os
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Tuple

from openai import OpenAI, APIError, APIConnectionError, RateLimitError, APITimeoutError
from dotenv import load_dotenv
from schemas import EnrichResponse, ResponseMeta, CategoryEnum, DepthEnum, FlagEnum

# Load environment variables from local .env
load_dotenv()

# Logging Setup
logger = logging.getLogger("LLMClient")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s'))
    logger.addHandler(handler)

BASE_DIR = Path(__file__).resolve().parent
PROMPTS_DIR = BASE_DIR / "prompts"
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)
QUARANTINE_FILE = LOGS_DIR / "quarantine.jsonl"
COST_LOG_FILE = LOGS_DIR / "cost.jsonl"


class LLMTimeoutException(Exception):
    """Raised when LLM call times out after max retries."""
    pass


class LLMAuthenticationException(Exception):
    """Raised on HTTP 401/403 invalid API key (never retried)."""
    pass


class SchemaValidationException(Exception):
    """Raised when model response fails schema validation after repair retry."""
    def __init__(self, message: str, raw_output: str, error_details: str):
        super().__init__(message)
        self.raw_output = raw_output
        self.error_details = error_details


class LLMClient:
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY", "dummy_key_for_stub_or_dev")
        self.base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        self.model_id = os.getenv("OPENROUTER_MODEL_ID", "openrouter/free")
        self.timeout = float(os.getenv("LLM_TIMEOUT_SECONDS", "30.0"))
        
        # Initialize OpenAI compatible client with hard timeout
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout,
            max_retries=0  # We handle explicit backoff and jitter manually to avoid un-bounded SDK loops
        )

    def load_system_prompt(self, version: str = "v1") -> str:
        prompt_file = PROMPTS_DIR / f"{version}.txt"
        if not prompt_file.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_file}")
        return prompt_file.read_text(encoding="utf-8")

    def _is_stub_mode(self) -> bool:
        return os.getenv("LLM_STUB", "0").lower() in ("1", "true", "yes")

    def _is_kill_switch_active(self) -> bool:
        enabled = os.getenv("LLM_ENABLED", "true").lower()
        return enabled in ("0", "false", "no", "off")

    def _calculate_cost_micro_cents(self, input_tokens: int, output_tokens: int) -> int:
        # Pinned OpenRouter micro-cents rate:
        # Input: 150 micro-cents per 1,000 tokens ($0.0015 / 1k)
        # Output: 600 micro-cents per 1,000 tokens ($0.0060 / 1k)
        input_cost = (input_tokens * 150 + 999) // 1000
        output_cost = (output_tokens * 600 + 999) // 1000
        return input_cost + output_cost

    def _write_cost_log(self, prompt_version: str, input_tokens: int, output_tokens: int, duration_ms: int, repair_count: int, status: str):
        cost_micro = self._calculate_cost_micro_cents(input_tokens, output_tokens)
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "prompt_version": prompt_version,
            "model_id": self.model_id,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_micro_cents": cost_micro,
            "duration_ms": duration_ms,
            "repair_count": repair_count,
            "status": status
        }
        # Log to stdout (12-Factor App)
        logger.info(f"COST_LOG: {json.dumps(log_entry)}")
        # Append to cost.jsonl
        with open(COST_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")

    def _write_quarantine_log(self, input_text: str, raw_output: str, error_reason: str, prompt_version: str):
        quarantine_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "prompt_version": prompt_version,
            "model_id": self.model_id,
            "input_text": input_text,
            "raw_output": raw_output,
            "error_reason": error_reason
        }
        logger.warning(f"QUARANTINE_LOG: {json.dumps(quarantine_entry)}")
        with open(QUARANTINE_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(quarantine_entry) + "\n")

    def _call_api_with_retry(self, messages: list) -> Tuple[str, int, int]:
        """Executes LLM request with selective exponential backoff on 429/5xx/timeouts."""
        max_attempts = 3
        backoff_delays = [1.0, 2.0, 4.0]
        
        for attempt in range(max_attempts):
            try:
                response = self.client.chat.completions.create(
                    model=self.model_id,
                    messages=messages,
                    temperature=0.1
                )
                raw_text = response.choices[0].message.content or ""
                usage = response.usage
                input_tokens = usage.prompt_tokens if usage else 0
                output_tokens = usage.completion_tokens if usage else 0
                return raw_text, input_tokens, output_tokens

            except (APITimeoutError, APIConnectionError) as e:
                logger.warning(f"Network/Timeout error on attempt {attempt+1}/{max_attempts}: {e}")
                if attempt == max_attempts - 1:
                    raise LLMTimeoutException(f"LLM API call timed out after {max_attempts} attempts: {e}")
                delay = backoff_delays[attempt] + random.uniform(0.1, 0.5)
                time.sleep(delay)

            except RateLimitError as e:
                logger.warning(f"Rate limit 429 hit on attempt {attempt+1}/{max_attempts}: {e}")
                if attempt == max_attempts - 1:
                    raise LLMTimeoutException(f"Rate limit exceeded after retries: {e}")
                # Obey Retry-After if present, otherwise exponential backoff + jitter
                delay = backoff_delays[attempt] + random.uniform(0.1, 0.5)
                time.sleep(delay)

            except APIError as e:
                # HTTP 401 / 403 Authentication or Permission Errors -> NEVER RETRY!
                if e.status_code in (401, 403):
                    logger.error(f"Authentication failure (HTTP {e.status_code}): {e.message}. Failing immediately without retry.")
                    raise LLMAuthenticationException(f"Invalid API Key or unauthorized access (HTTP {e.status_code}): {e.message}")
                # 5xx Server errors -> Retry
                elif e.status_code and e.status_code >= 500:
                    logger.warning(f"Server error 5xx (HTTP {e.status_code}) on attempt {attempt+1}/{max_attempts}: {e.message}")
                    if attempt == max_attempts - 1:
                        raise LLMTimeoutException(f"Server error {e.status_code} after retries: {e.message}")
                    delay = backoff_delays[attempt] + random.uniform(0.1, 0.5)
                    time.sleep(delay)
                else:
                    raise e

        raise LLMTimeoutException("LLM call failed after maximum retries.")

    def enrich_content(self, input_text: str, prompt_version: str = "v1") -> Tuple[EnrichResponse, ResponseMeta]:
        start_time = time.time()

        # 1. Stub Mode Check (LLM_STUB=1)
        if self._is_stub_mode():
            logger.info("LLM_STUB=1 active. Returning schema-valid mock response.")
            duration_ms = int((time.time() - start_time) * 1000)
            mock_data = EnrichResponse(
                category=CategoryEnum.ENGINEERING,
                summary="Mock stub response for content enrichment testing.",
                technical_depth=DepthEnum.INTERMEDIATE,
                quality_flags=[FlagEnum.CONTAINS_CODE],
                confidence=0.99,
                reason="Generated via deterministic LLM_STUB mode."
            )
            meta = ResponseMeta(
                prompt_version=prompt_version,
                model_id=self.model_id,
                duration_ms=duration_ms,
                input_tokens=0,
                output_tokens=0,
                cost_micro_cents=0,
                repair_count=0,
                stub_mode=True,
                kill_switch_active=False
            )
            return mock_data, meta

        # 2. Kill Switch Check (LLM_ENABLED=false)
        if self._is_kill_switch_active():
            logger.info("LLM_ENABLED=false active. Kill switch engaged. Returning fallback response.")
            duration_ms = int((time.time() - start_time) * 1000)
            fallback_data = EnrichResponse(
                category=CategoryEnum.OTHER,
                summary="Content processing skipped due to active system maintenance kill switch.",
                technical_depth=DepthEnum.BEGINNER,
                quality_flags=[FlagEnum.NEEDS_REVIEW],
                confidence=0.0,
                reason="LLM_ENABLED=false kill switch active."
            )
            meta = ResponseMeta(
                prompt_version=prompt_version,
                model_id=self.model_id,
                duration_ms=duration_ms,
                input_tokens=0,
                output_tokens=0,
                cost_micro_cents=0,
                repair_count=0,
                stub_mode=False,
                kill_switch_active=True
            )
            return fallback_data, meta

        # 3. Live LLM Call with 1-Shot Repair Retry Loop
        system_prompt = self.load_system_prompt(prompt_version)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": input_text}
        ]

        total_input_tokens = 0
        total_output_tokens = 0
        repair_count = 0

        # --- Attempt 1 ---
        raw_text, in_tok, out_tok = self._call_api_with_retry(messages)
        total_input_tokens += in_tok
        total_output_tokens += out_tok

        # Strip potential markdown codeblock formatting if present
        clean_text = raw_text.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        if clean_text.startswith("```"):
            clean_text = clean_text[3:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]
        clean_text = clean_text.strip()

        try:
            parsed_data = EnrichResponse.model_validate_json(clean_text)
            duration_ms = int((time.time() - start_time) * 1000)
            cost_micro = self._calculate_cost_micro_cents(total_input_tokens, total_output_tokens)
            self._write_cost_log(prompt_version, total_input_tokens, total_output_tokens, duration_ms, repair_count=0, status="success")

            meta = ResponseMeta(
                prompt_version=prompt_version,
                model_id=self.model_id,
                duration_ms=duration_ms,
                input_tokens=total_input_tokens,
                output_tokens=total_output_tokens,
                cost_micro_cents=cost_micro,
                repair_count=0,
                stub_mode=False,
                kill_switch_active=False
            )
            return parsed_data, meta

        except Exception as first_error:
            repair_count = 1
            error_msg = str(first_error)
            logger.warning(f"Schema validation failed on Attempt 1: {error_msg}. Initiating 1-shot repair retry.")

            # --- Attempt 2 (Repair Retry) ---
            repair_messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": input_text},
                {"role": "assistant", "content": raw_text},
                {
                    "role": "user",
                    "content": f"Your previous answer was rejected for reason: {error_msg}. Return ONLY valid raw JSON matching the required schema with zero codeblocks or commentary."
                }
            ]

            try:
                raw_text_2, in_tok_2, out_tok_2 = self._call_api_with_retry(repair_messages)
                total_input_tokens += in_tok_2
                total_output_tokens += out_tok_2

                clean_text_2 = raw_text_2.strip()
                if clean_text_2.startswith("```json"):
                    clean_text_2 = clean_text_2[7:]
                if clean_text_2.startswith("```"):
                    clean_text_2 = clean_text_2[3:]
                if clean_text_2.endswith("```"):
                    clean_text_2 = clean_text_2[:-3]
                clean_text_2 = clean_text_2.strip()

                parsed_data_2 = EnrichResponse.model_validate_json(clean_text_2)
                duration_ms = int((time.time() - start_time) * 1000)
                cost_micro = self._calculate_cost_micro_cents(total_input_tokens, total_output_tokens)
                self._write_cost_log(prompt_version, total_input_tokens, total_output_tokens, duration_ms, repair_count=1, status="repaired")

                meta = ResponseMeta(
                    prompt_version=prompt_version,
                    model_id=self.model_id,
                    duration_ms=duration_ms,
                    input_tokens=total_input_tokens,
                    output_tokens=total_output_tokens,
                    cost_micro_cents=cost_micro,
                    repair_count=1,
                    stub_mode=False,
                    kill_switch_active=False
                )
                return parsed_data_2, meta

            except Exception as second_error:
                duration_ms = int((time.time() - start_time) * 1000)
                final_error_msg = f"Attempt 1 error: {first_error} | Attempt 2 repair error: {second_error}"
                logger.error(f"Repair retry failed: {final_error_msg}. Quarantine logging initiated.")

                # Write to logs/quarantine.jsonl
                self._write_quarantine_log(
                    input_text=input_text,
                    raw_output=raw_text_2 if 'raw_text_2' in locals() else raw_text,
                    error_reason=final_error_msg,
                    prompt_version=prompt_version
                )
                self._write_cost_log(prompt_version, total_input_tokens, total_output_tokens, duration_ms, repair_count=1, status="quarantined")

                raise SchemaValidationException(
                    message="Model failed to produce valid JSON matching the schema after 1-shot repair retry.",
                    raw_output=raw_text_2 if 'raw_text_2' in locals() else raw_text,
                    error_details=final_error_msg
                )
