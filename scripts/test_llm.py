#!/usr/bin/env python3
"""LLM Provider Diagnostic & Batch Verification Tool

Usage:
  uv run python scripts/test_llm.py
  uv run python scripts/test_llm.py --batch 3
"""

import argparse
import asyncio
import sys
import time

from mei.application.services.extraction import ExtractionResult
from mei.infrastructure.llm.factory import get_structured_llm
from mei.shared.config import get_settings


async def run_single_test(llm, idx: int = 1, text: str = "Test event.") -> tuple[int, bool, float, str]:
    start = time.perf_counter()
    try:
        res = await llm.generate_structured(
            task_name="claim_event_extraction",
            prompt_version="claims_events_v1",
            input_text=text,
            output_model=ExtractionResult,
            metadata={"test_idx": str(idx)},
        )
        elapsed = time.perf_counter() - start
        summary = f"Parsed {len(res.claims)} claim(s), {len(res.events)} event(s)"
        return idx, True, elapsed, summary
    except Exception as exc:
        elapsed = time.perf_counter() - start
        return idx, False, elapsed, f"{type(exc).__name__}: {exc}"


async def main() -> int:
    parser = argparse.ArgumentParser(description="Test LLM provider connectivity and queue/rate limiting.")
    parser.add_argument(
        "--batch",
        type=int,
        default=1,
        help="Number of concurrent requests to launch simultaneously in batch mode (default: 1)",
    )
    args = parser.parse_args()

    settings = get_settings()
    print("=" * 70)
    print("MEI Platform LLM Provider Diagnostic")
    print("=" * 70)
    print(f"Provider:                {settings.llm_provider}")
    print(f"Model:                   {settings.llm_model}")
    print(f"Base URL:                {settings.llm_base_url or '(default for provider)'}")
    print(f"API Key configured:      {'Yes' if bool(settings.llm_api_key) else 'No'}")
    print(f"Max Concurrency:         {settings.llm_max_concurrency or '(auto)'}")
    print(f"Min Request Interval:    {settings.llm_min_request_interval_seconds}s")
    print(f"Max Retries:             {settings.llm_max_retries}")
    print("=" * 70)

    try:
        llm = get_structured_llm()
    except Exception as exc:
        print(f"❌ Failed to initialize LLM adapter: {exc}")
        return 1

    sample_texts = [
        "On October 12, Foreign Minister Jane Doe announced bilateral trade agreements in Geneva.",
        "Naval security forces reported intercepted drone activity near the Bab el-Mandeb strait yesterday.",
        "Diplomatic delegations met in Muscat to discuss cease-fire monitoring protocols on Tuesday.",
        "Regional energy authorities confirmed temporary oil terminal maintenance in Fujairah.",
        "Border monitoring checkpoints expanded surveillance operations across the northern corridor.",
    ]

    count = max(1, args.batch)
    if count == 1:
        print("\n🚀 Executing single extraction test...")
        idx, ok, elapsed, detail = await run_single_test(llm, 1, sample_texts[0])
        if ok:
            print(f"✅ SUCCESS ({elapsed:.2f}s): {detail}")
            return 0
        else:
            print(f"❌ FAILED ({elapsed:.2f}s): {detail}")
            return 1
    else:
        print(f"\n🚀 Launching {count} SIMULTANEOUS requests to test queue & rate limiting...")
        tasks = [
            run_single_test(llm, i + 1, sample_texts[i % len(sample_texts)])
            for i in range(count)
        ]
        overall_start = time.perf_counter()
        results = await asyncio.gather(*tasks)
        overall_elapsed = time.perf_counter() - overall_start

        print("\nBatch Results:")
        print("-" * 70)
        success_count = 0
        for idx, ok, elapsed, detail in results:
            status = "✅ SUCCESS" if ok else "❌ FAILED"
            print(f"  Request #{idx:02d}: {status} in {elapsed:.2f}s -> {detail}")
            if ok:
                success_count += 1
        print("-" * 70)
        print(f"Summary: {success_count}/{count} succeeded in {overall_elapsed:.2f}s total.")
        return 0 if success_count == count else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
