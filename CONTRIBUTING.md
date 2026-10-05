# Contributing to Long Mission

Thanks for helping improve a small, evidence-first protocol for long-running AI-agent work.

## Before opening an issue

- Search existing issues and discussions.
- Include the mission profile, command, Python version, and the smallest reproducible ledger.
- Never include API keys, tokens, private prompts, or private repository data.

## Before opening a pull request

1. Explain the user-visible outcome or protocol invariant.
2. Keep implementation routes replaceable; do not hard-code a project, provider, port, or UI.
3. Add or update protocol tests for changed behavior.
4. Run:

   ```bash
   python3 -m pytest -q tests test_long_mission_protocol.py
   python3 -m compileall -q scripts
   ```

5. Update `CHANGELOG.md` and `CHANGELOG-中文.md` when behavior changes.
6. Include failure evidence and the acceptance result in the pull request.

## Good first contributions

- Add a fixture for a failed runner iteration;
- improve a bilingual ledger message;
- add a reference/UI acceptance example;
- improve documentation or a reproducible demo;
- add a new runtime-truth or evidence adapter.

## Design rule

Long Mission governs outcomes, evidence, and safe continuation. It should not force a particular framework, renderer, model provider, or repository layout.
