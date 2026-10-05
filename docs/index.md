---
layout: default
title: Long Mission
description: Evidence-backed continuation for long-running AI agents.
---

# Long Mission

## Evidence-backed continuation for AI agents

Long Mission is a small, runtime-agnostic protocol for tasks that must continue across failures, context windows, tools, and verification steps.

```text
Contract → Explore → Execute → Verify → Replan → Close
```

## The problem

Long-running agents tend to either follow a bad plan too literally or stop early and claim success without independent proof. Long Mission keeps the outcome fixed, keeps the implementation route replaceable, and requires evidence before completion.

## What it adds

- Explicit user confirmation before execution;
- durable mission and progress ledgers;
- bounded exploration and evidence-backed replanning;
- independent acceptance and runtime-parity gates;
- real-user-surface checks for UI work;
- adaptive visual loops with capability-ceiling detection;
- targeted research after non-trivial failures;
- bilingual reports and inspectable completion receipts.

## Try it

```bash
git clone https://github.com/ccygod/long-mission.git
cd long-mission
python3 scripts/mission_start.py .long-mission/demo \
  --non-interactive \
  --objective "Run a small verified task" \
  --deliverable "demo-output.txt" \
  --acceptance "the output exists and the check passes"
```

The mission intentionally waits for explicit confirmation before execution. Read the full protocol in the [README](https://github.com/ccygod/long-mission) and browse the [release history](https://github.com/ccygod/long-mission/blob/main/CHANGELOG.md).

## Learn more

- [README](https://github.com/ccygod/long-mission)
- [中文说明](https://github.com/ccygod/long-mission/blob/main/README-%E4%B8%AD%E6%96%87.md)
- [Discussions](https://github.com/ccygod/long-mission/discussions)
- [Contributing](https://github.com/ccygod/long-mission/blob/main/CONTRIBUTING.md)
