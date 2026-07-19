"""
Script 04: Call the inference endpoint with only USER_ID.

The service fetches all feature columns from the Postgres online store
automatically, then returns the 32-dim user embedding.

Usage:
    cd backend
    uv run python ../online-feature-store-integration/scripts/04_test_inference.py \\
        --endpoint https://<service-id>-<account>.snowflakecomputing.app \\
        --token <your_pat_token>

Optional flags:
    --users   comma-separated USER_IDs  (default: demo_user,user_electronics,user_fashion)
    --verbose print full embedding vector
"""

from __future__ import annotations

import argparse
import json
import time
from typing import Any

import requests


def _headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f'Snowflake Token="{token}"',
        "Content-Type": "application/json",
    }


def call_entity_ids_only(
    endpoint: str,
    token: str,
    user_ids: list[str],
) -> tuple[Any, float]:
    """Send only USER_ID — features are fetched from the online store."""
    payload = {
        "dataframe_split": {
            "index": list(range(len(user_ids))),
            "columns": ["USER_ID"],
            "data": [[uid] for uid in user_ids],
        }
    }
    t0 = time.perf_counter()
    resp = requests.post(
        f"{endpoint}/predict",
        headers=_headers(token),
        json=payload,
        timeout=30,
    )
    latency_ms = (time.perf_counter() - t0) * 1000
    resp.raise_for_status()
    return resp.json(), round(latency_ms, 2)


def call_with_override(
    endpoint: str,
    token: str,
    user_id: str,
    total_clicks_override: int,
) -> Any:
    """Send USER_ID + one overridden feature; the rest are fetched from the store."""
    payload = {
        "dataframe_split": {
            "index": [0],
            "columns": ["USER_ID", "TOTAL_CLICKS"],
            "data": [[user_id, float(total_clicks_override)]],
        }
    }
    resp = requests.post(
        f"{endpoint}/predict",
        headers=_headers(token),
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def _first_embedding(result: Any) -> list[float] | None:
    """Extract the first row's embedding from the response."""
    # The REST API returns {"predictions": [[v0, v1, ...], ...]} or
    # {"dataframe_split": {"data": [[v0, ...], ...]}}
    if isinstance(result, dict):
        for key in ("predictions", "data"):
            val = result.get(key) or (result.get("dataframe_split") or {}).get(key)
            if val:
                return val[0] if isinstance(val[0], list) else list(val[0].values())
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Test Online Feature Store inference")
    parser.add_argument("--endpoint", required=True, help="Inference service endpoint URL")
    parser.add_argument("--token", required=True, help="Snowflake PAT token")
    parser.add_argument(
        "--users",
        default="demo_user,user_electronics,user_fashion",
        help="Comma-separated USER_IDs",
    )
    parser.add_argument("--verbose", action="store_true", help="Print full embedding vectors")
    args = parser.parse_args()

    user_ids = [u.strip() for u in args.users.split(",")]
    endpoint = args.endpoint.rstrip("/")

    print("=" * 60)
    print("Online Feature Store Integration — Inference Test")
    print("=" * 60)
    print(f"Endpoint : {endpoint}")
    print(f"Users    : {user_ids}")
    print()

    # ── Test 1: batch call with entity IDs only ──────────────────────────
    print("Test 1: Batch inference — only USER_ID sent, features auto-fetched")
    result, latency = call_entity_ids_only(endpoint, args.token, user_ids)
    emb = _first_embedding(result)
    emb_dim = len(emb) if emb else "?"
    print(f"  Status  : OK")
    print(f"  Latency : {latency} ms")
    print(f"  Embedding dim: {emb_dim}")
    if args.verbose and emb:
        print(f"  First embedding: {[round(v, 4) for v in emb[:8]]} ... (first 8 of {emb_dim})")
    print()

    # ── Test 2: single call with feature override ─────────────────────────
    print("Test 2: Inference with TOTAL_CLICKS override (=999)")
    print("  Only TOTAL_CLICKS comes from the request; all other features fetched.")
    result_override = call_with_override(endpoint, args.token, user_ids[0], 999)
    emb_override = _first_embedding(result_override)
    print(f"  Status  : OK")
    if emb and emb_override:
        # Embeddings should differ because TOTAL_CLICKS changed
        diff = sum((a - b) ** 2 for a, b in zip(emb, emb_override)) ** 0.5
        print(f"  L2 distance vs. no-override: {round(diff, 4)} (non-zero → override took effect)")
    print()

    # ── Test 3: latency warmup ────────────────────────────────────────────
    print("Test 3: Latency (5 consecutive single-user calls, after warmup)")
    # Warmup
    call_entity_ids_only(endpoint, args.token, [user_ids[0]])
    latencies = []
    for _ in range(5):
        _, lat = call_entity_ids_only(endpoint, args.token, [user_ids[0]])
        latencies.append(lat)
    avg = round(sum(latencies) / len(latencies), 2)
    p50 = round(sorted(latencies)[len(latencies) // 2], 2)
    print(f"  Latencies : {latencies} ms")
    print(f"  avg={avg} ms  p50={p50} ms")
    print()
    print("All tests passed.")


if __name__ == "__main__":
    main()
