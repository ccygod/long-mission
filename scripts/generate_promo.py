#!/usr/bin/env python3
"""Generate a release promotion pack, with an optional OpenAI rewrite."""
from __future__ import annotations

import argparse
import json
import os
import urllib.request
from pathlib import Path


def template(tag: str, url: str, body: str) -> str:
    summary = body.strip()[:1200] or "Long Mission adds evidence-backed continuation and safe completion for long-running AI-agent work."
    return f"""# Release promotion pack: {tag}

## Hacker News / technical community

**Show HN: Long Mission {tag} — verification and continuation for AI agents**

Long-running agents often stop early, repeat a failed route, or claim completion without independent proof. Long Mission keeps the outcome contract fixed while allowing implementation routes to change when evidence falsifies them.

This release adds or maintains: explicit user confirmation, bounded exploration, independent acceptance gates, adaptive visual stopping, bilingual progress feedback, and failure research before retry.

Release: {url}

## Reddit / community

I built Long Mission to address a recurring agent failure mode: a model says “done” even though the user-visible result or evidence is incomplete.

The project is a small, runtime-agnostic protocol rather than another agent framework. It records the contract, retries with evidence, supports replanning, and refuses completion without an independent gate.

{summary}

{url}

## LinkedIn

Long-running AI-agent work needs more than a plan. Long Mission adds explicit contracts, safe replanning, independent verification, adaptive visual/UI checks, and evidence-backed completion receipts.

Release {tag}: {url}

## X / short post

Agents should not be able to say “done” without proof. Long Mission adds contracts, safe replanning, adaptive verification, and completion receipts for long-running AI-agent work. {url}
"""


def ai_rewrite(tag: str, url: str, body: str, fallback: str) -> str:
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        return fallback
    model = os.environ.get("OPENAI_MODEL", "gpt-5-mini")
    prompt = "Rewrite the following release notes into a concise, non-spammy launch pack with sections Hacker News, Reddit, LinkedIn, and X. Preserve factual claims only. Include the release URL. Return Markdown only.\n\n" + body
    payload = json.dumps({"model": model, "input": prompt}).encode()
    request = urllib.request.Request("https://api.openai.com/v1/responses", data=payload, headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            data = json.loads(response.read().decode())
        output = data.get("output_text")
        return output.strip() if isinstance(output, str) and output.strip() else fallback
    except Exception:
        return fallback


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", required=True)
    parser.add_argument("--url", required=True)
    parser.add_argument("--body-file", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    body = args.body_file.read_text(encoding="utf-8") if args.body_file.exists() else ""
    fallback = template(args.tag, args.url, body)
    result = ai_rewrite(args.tag, args.url, body, fallback)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(result + "\n", encoding="utf-8")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
