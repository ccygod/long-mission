# Launch Kit

This page contains reusable, non-spam launch copy for Long Mission.

## One-sentence description

Long Mission is an outcome-driven control protocol for long-running AI-agent work: explicit contracts, independent verification, safe replanning, and evidence-backed completion receipts.

## Show HN draft

**Title:** Show HN: Long Mission — a verification and continuation protocol for AI agents

**Post:**

Long-running agents usually fail in one of two ways: they follow a bad plan too literally, or they stop early and claim success without proof. Long Mission keeps the outcome contract fixed while allowing the implementation route to change when evidence falsifies it.

The protocol adds user confirmation, bounded exploration, independent acceptance gates, real-user-surface checks for UI work, artifact/runtime parity, failure research before retry, and bilingual mission reports. It is runtime-agnostic Python and does not require a particular model, framework, or orchestration stack.

Repository: https://github.com/ccygod/long-mission

## Reddit / community post draft

I built Long Mission after seeing agents repeatedly stop early or repeat the same failed fix. It is a small control protocol rather than another agent framework: lock the outcome, keep the route replaceable, require evidence before completion, and make failures visible.

The interesting part is the acceptance gate: “the model said done” is not evidence. Visual/UI tasks, runtime parity, reference-image capability limits, and failure research are separate conditional gates.

Feedback is welcome, especially on mission adapters, failure fixtures, and real-world agent workflows.

## Short social thread

1. An agent saying “done” is not a completion proof.
2. A plan is a hypothesis; a failed route should be replaced without changing the user’s outcome.
3. Long Mission records the contract, evidence, replans, failures, and final completion receipt.
4. UI work gets real-surface evidence; non-trivial failures trigger targeted research before retry.
5. https://github.com/ccygod/long-mission
