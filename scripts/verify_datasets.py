#!/usr/bin/env python3
"""
Smoke-test JSON datasets against a running FastAPI backend.

Usage:
  python scripts/verify_datasets.py
  python scripts/verify_datasets.py --base-url http://127.0.0.1:8000

Exit code 0 if all requests succeed (HTTP 2xx).
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DATASETS_DIR = REPO_ROOT / "datasets"


def load_dataset_files() -> list[Path]:
    return sorted(DATASETS_DIR.glob("dataset_*.json"))


def post_json(base: str, path: str, body: dict) -> tuple[int, str]:
    url = base.rstrip("/") + path
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace")


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify datasets against VC Analyst API.")
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:8000",
        help="FastAPI root URL (default: http://127.0.0.1:8000)",
    )
    args = parser.parse_args()
    base = args.base_url

    files = load_dataset_files()
    if not files:
        print(f"No dataset_*.json files under {DATASETS_DIR}", file=sys.stderr)
        return 1

    failed = False
    for fp in files:
        spec = json.loads(fp.read_text(encoding="utf-8"))
        test = spec.get("api_smoke_test")
        if not test:
            print(f"[skip] {fp.name}: no api_smoke_test")
            continue
        path = test["path"]
        body = test["body"]
        code, _text = post_json(base, path, body)
        ok = 200 <= code < 300
        status = "OK" if ok else "FAIL"
        print(f"[{status}] {fp.name}  {test.get('method', 'POST')} {path}  -> HTTP {code}")
        if not ok:
            failed = True

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
