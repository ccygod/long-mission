# Changelog

All notable changes to Long Mission are documented here.

The format follows the Keep a Changelog convention. Git tags are the immutable version markers; `VERSION` is the machine-readable current version.

## [1.0.11] - 2026-10-05

### Added

- Added bilingual `CHANGELOG.md` companion documentation and clarified the release/versioning model.
- Added explicit `mission_confirm.py` confirmation receipts; `--confirmed` self-confirmation is no longer accepted.
- Added adaptive visual-loop stopping: pass early, replan after consecutive no-improvement attempts, and use a configurable safety cap instead of a fixed ten-attempt completion rule.
- Added per-iteration `feedback.jsonl` records and bilingual progress feedback for all supervised mission types.
- Added failure-research evidence through `--research-source` and `--research-summary`.

### Changed

- Acceptance and launch gates now require a confirmation receipt, not only a mutable state flag.
- README and Chinese README now describe the current 1.0.10/1.0.11 protocol evolution and release workflow.

## [1.0.10] - 2026-10-05

### Added

- Added adaptive reference/UI capability checks, `blocked_engine`, reference acceptance matrices, and bilingual mission ledgers.
- Added universal iteration feedback and failure-research rules to the Skill protocol.

## [1.0.7] - 2026-10-04

### Changed

- Bound supervisor iterations and recorded retry outcomes.

## [1.0.6] - 2026-10-04

### Added

- Made the supervisor own continuation and added bilingual mission-report completion evidence.

## [1.0.2] - 2026-10-03

### Added

- Added visual/UI mission gates with real-surface evidence.

## [1.0.1] - 2026-10-03

### Added

- Added runtime truth, PRD audit, and stronger independent completion checks.

