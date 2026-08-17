# run_eval.py — Automated 8-Case Evaluation Benchmark Runner

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add parent directory to sys.path so we can import llm_client and schemas
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from llm_client import LLMClient


def run_benchmark():
    eval_dir = Path(__file__).resolve().parent
    cases_file = eval_dir / "cases.json"
    
    if not cases_file.exists():
        print(f"Error: {cases_file} not found.")
        sys.exit(1)
        
    with open(cases_file, "r", encoding="utf-8") as f:
        cases = json.load(f)
        
    client = LLMClient()
    prompt_version = "v1"
    
    print("=" * 70)
    print(f"RUNNING EVALUATION BENCHMARK — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"Model ID: {client.model_id} | Prompt Version: {prompt_version} | Stub Mode: {client._is_stub_mode()}")
    print("=" * 70)
    
    total_cases = len(cases)
    category_correct = 0
    depth_correct = 0
    results = []
    
    for case in cases:
        case_id = case["id"]
        desc = case["description"]
        text_input = case["input"]
        expected_cat = case["expected_category"]
        expected_depth = case["expected_technical_depth"]
        
        try:
            response, meta = client.enrich_content(text_input, prompt_version=prompt_version)
            actual_cat = response.category.value
            actual_depth = response.technical_depth.value
            
            cat_match = (actual_cat == expected_cat)
            depth_match = (actual_depth == expected_depth)
            
            if cat_match:
                category_correct += 1
            if depth_match:
                depth_correct += 1
                
            status_symbol = "✅ PASS" if cat_match else "❌ FAIL"
            print(f"[{status_symbol}] Case {case_id}: {desc}")
            print(f"     Expected Category: {expected_cat:<15} | Actual: {actual_cat}")
            print(f"     Expected Depth:    {expected_depth:<15} | Actual: {actual_depth}")
            print(f"     Confidence: {response.confidence:.2f} | Cost: {meta.cost_micro_cents} µ-cents | Duration: {meta.duration_ms}ms")
            print(f"     Reason: {response.reason}")
            print("-" * 70)
            
            results.append({
                "case_id": case_id,
                "description": desc,
                "expected_category": expected_cat,
                "actual_category": actual_cat,
                "category_pass": cat_match,
                "expected_depth": expected_depth,
                "actual_depth": actual_depth,
                "depth_pass": depth_match,
                "confidence": response.confidence,
                "cost_micro_cents": meta.cost_micro_cents,
                "duration_ms": meta.duration_ms
            })
            
        except Exception as e:
            print(f"[❌ ERROR] Case {case_id}: {desc} — Error: {e}")
            print("-" * 70)
            results.append({
                "case_id": case_id,
                "description": desc,
                "expected_category": expected_cat,
                "actual_category": "ERROR",
                "category_pass": False,
                "error": str(e)
            })

    category_accuracy = (category_correct / total_cases) * 100
    depth_accuracy = (depth_correct / total_cases) * 100
    
    print("=" * 70)
    print("BENCHMARK ACCURACY SUMMARY")
    print(f"Total Test Cases:        {total_cases}")
    print(f"Category Accuracy:       {category_correct}/{total_cases} ({category_accuracy:.1f}%)")
    print(f"Technical Depth Accuracy: {depth_correct}/{total_cases} ({depth_accuracy:.1f}%)")
    print("=" * 70)
    
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "prompt_version": prompt_version,
        "model_id": client.model_id,
        "total_cases": total_cases,
        "category_accuracy_percent": category_accuracy,
        "depth_accuracy_percent": depth_accuracy,
        "results": results
    }
    
    report_file = eval_dir / "eval_report.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"Full benchmark report saved to {report_file}")


if __name__ == "__main__":
    run_benchmark()
