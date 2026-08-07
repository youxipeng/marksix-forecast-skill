#!/usr/bin/env python3
"""Thin client for a privately hosted Mark Six Pro service."""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path


def api_url(args: argparse.Namespace) -> str:
    base = (args.api_url or os.getenv("MARKSIX_PRO_API_URL") or "").rstrip("/")
    if not base:
        raise SystemExit("缺少 MARKSIX_PRO_API_URL / --api-url")
    return base


def api_config(args: argparse.Namespace) -> tuple[str, str]:
    base = api_url(args)
    key = args.api_key or os.getenv("MARKSIX_PRO_API_KEY") or ""
    if not key:
        raise SystemExit("缺少 MARKSIX_PRO_API_KEY / --api-key")
    return base, key


def load_history(path: str) -> list[dict]:
    with Path(path).open("r", encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))
    required = {"draw_id", "date", "n1", "n2", "n3", "n4", "n5", "n6", "extra"}
    if not rows:
        raise SystemExit("历史 CSV 为空")
    missing = required - set(rows[0])
    if missing:
        raise SystemExit(f"历史 CSV 缺少字段: {', '.join(sorted(missing))}")
    return [{k: row[k] for k in required} for row in rows]


def post_json(url: str, key: str, payload: dict) -> dict:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json", "X-API-Key": key},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            detail = json.loads(raw)
        except json.JSONDecodeError:
            detail = {"detail": raw or exc.reason}
        if exc.code == 402:
            print(json.dumps(detail, ensure_ascii=False, indent=2), file=sys.stderr)
            raise SystemExit(2)
        raise SystemExit(f"API {exc.code}: {json.dumps(detail, ensure_ascii=False)}")


def register_key(url: str) -> dict:
    req = urllib.request.Request(
        f"{url}/v1/register",
        data=b"{}",
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise SystemExit(f"注册失败 API {exc.code}: {exc.read().decode('utf-8', errors='replace')}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Mark Six Pro private API client")
    sub = ap.add_subparsers(dest="command", required=True)
    register = sub.add_parser("register")
    register.add_argument("--api-url")
    forecast = sub.add_parser("forecast")
    forecast.add_argument("--history", required=True)
    forecast.add_argument("--target", required=True)
    forecast.add_argument("--tickets", type=int, default=8)
    forecast.add_argument("--output")
    forecast.add_argument("--api-url")
    forecast.add_argument("--api-key")
    args = ap.parse_args()

    if args.command == "register":
        print(json.dumps(register_key(api_url(args)), ensure_ascii=False, indent=2))
        return

    base, key = api_config(args)
    payload = {
        "target": args.target,
        "tickets": args.tickets,
        "draws": load_history(args.history),
    }
    result = post_json(f"{base}/v1/forecast", key, payload)
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
        print(args.output)
    else:
        print(text)


if __name__ == "__main__":
    main()
