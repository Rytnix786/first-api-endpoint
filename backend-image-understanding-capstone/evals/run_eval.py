# evals/run_eval.py — Evaluation Benchmark Runner for Top-1 Precision & Mismatch Guard Accuracy

import os
import sys
import json
import time
from pathlib import Path
from sqlalchemy.orm import sessionmaker

# Add parent directory to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Ensure UTF-8 output on Windows terminal
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from database import engine, init_db
from models import BlogPost, ImageItem
from services.matching_service import MatchingService
from services.mismatch_guard import MismatchGuard
from services.embedding_service import EmbeddingService
from seed import seed_database

EVAL_CASES_PATH = BASE_DIR / "evals" / "eval_dataset.json"
REPORT_OUTPUT_PATH = BASE_DIR / "evals" / "eval_report.json"


def run_evaluation():
    seed_database()
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    matching_service = MatchingService()
    mismatch_guard = MismatchGuard()

    with open(EVAL_CASES_PATH, "r", encoding="utf-8") as f:
        cases = json.load(f)

    print("======================================================================")
    print(f"RUNNING CAPSTONE EVALUATION BENCHMARK — {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}")
    print(f"Total Evaluation Cases: {len(cases)}")
    print("======================================================================")

    passed_count = 0
    results_detail = []

    for idx, case in enumerate(cases, 1):
        case_id = case["id"]
        post_id = case["post_id"]
        description = case["description"]

        post = db.query(BlogPost).filter(BlogPost.id == post_id).first()

        if "forced_candidate_id" in case:
            # Test direct guard evaluation on forced candidate (e.g. Wolf on Fox)
            candidate_img = db.query(ImageItem).filter(ImageItem.id == case["forced_candidate_id"]).first()
            post_vec = post.embedding or EmbeddingService.get_embedding(f"{post.title} {post.content} {post.target_subject}")
            img_vec = candidate_img.embedding or EmbeddingService.get_embedding(f"{candidate_img.subject} {candidate_img.caption}")
            sim = EmbeddingService.cosine_similarity(post_vec, img_vec)

            guard_pass, verdict, reason = mismatch_guard.evaluate_candidate(
                post_target_subject=post.target_subject,
                post_title=post.title,
                image_subject=candidate_img.subject,
                image_category=candidate_img.category,
                image_caption=candidate_img.caption,
                similarity_score=sim,
                model_confidence=candidate_img.confidence
            )

            is_pass = (verdict == case["expected_verdict"])
            if is_pass:
                passed_count += 1
                print(f"[✅ PASS] Case {idx}: {description}")
                print(f"     Forced Image: {candidate_img.id} ({candidate_img.subject}) | Verdict: {verdict} | Reason: {reason}")
            else:
                print(f"[❌ FAIL] Case {idx}: {description}")
                print(f"     Expected: {case['expected_verdict']} | Actual: {verdict}")

            results_detail.append({
                "case_id": case_id,
                "passed": is_pass,
                "type": "guard_refusal",
                "verdict": verdict,
                "reason": reason
            })

        else:
            # Full Top-1 Matching Evaluation
            match_res = matching_service.rank_and_evaluate_matches(db, post_id)

            if case.get("expected_has_confident_match") is False:
                is_pass = (match_res.has_confident_match is False)
                top_id = match_res.candidates[0].image_id if match_res.candidates else None
            else:
                top_id = match_res.candidates[0].image_id if match_res.candidates else None
                expected_ids = case.get("expected_top_image_ids", [case.get("expected_top_image_id")])
                is_pass = (top_id in expected_ids and match_res.has_confident_match is True)

            if is_pass:
                passed_count += 1
                print(f"[✅ PASS] Case {idx}: {description}")
                print(f"     Top Match: {top_id} | Confident: {match_res.has_confident_match} | Summary: {match_res.status_summary}")
            else:
                print(f"[❌ FAIL] Case {idx}: {description}")
                print(f"     Expected Top Image: {case.get('expected_top_image_ids') or case.get('expected_top_image_id')} | Actual Top Image: {top_id}")

            results_detail.append({
                "case_id": case_id,
                "passed": is_pass,
                "type": "top1_ranking",
                "top_image_id": top_id,
                "has_confident_match": match_res.has_confident_match
            })

        print("----------------------------------------------------------------------")

    precision = (passed_count / len(cases)) * 100.0
    print("======================================================================")
    print("BENCHMARK SUMMARY")
    print(f"Total Test Cases:   {len(cases)}")
    print(f"Passed Cases:       {passed_count} / {len(cases)}")
    print(f"Top-1 Precision:    {precision:.1f}%")
    print("======================================================================")

    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "total_cases": len(cases),
        "passed_cases": passed_count,
        "precision_pct": precision,
        "details": results_detail
    }

    with open(REPORT_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    db.close()
    return precision


if __name__ == "__main__":
    run_evaluation()
