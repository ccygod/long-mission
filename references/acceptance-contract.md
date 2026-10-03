# Acceptance Contract
# 验收契约

This reference defines the optional, generic verification contract consumed by
`scripts/acceptance_gate.py`. It intentionally contains no repository paths,
framework names, ports, providers, or product-specific labels.

## Basic checks

`state.json` may contain:

```json
{
  "acceptance_checks": [
    {"name": "unit tests", "command": ["python", "-m", "pytest", "-q"]}
  ]
}
```

Each check is an object with a non-empty `name` and an argv-style `command`
array. A string shell command is deliberately not accepted: keeping argv
explicit avoids hidden shell expansion and makes the check reproducible.

## Conditional verification gates

When a task needs stronger evidence, add `verification_gates`:

```json
{
  "verification_gates": [
    {
      "id": "real_user_surface",
      "required": true,
      "checks": [
        {"name": "fresh host interaction", "command": ["python", "scripts/ui_check.py"]}
      ],
      "evidence": ["evidence/ui-screenshot.png", "evidence/ui-accessibility.json"]
    },
    {
      "id": "artifact_parity",
      "required": true,
      "checks": [
        {"name": "source-build-runtime identity", "command": ["python", "scripts/parity_check.py"]}
      ],
      "evidence": ["evidence/parity.json"]
    },
    {
      "id": "process_memory",
      "required": false,
      "checks": [
        {"name": "trajectory and delivery", "command": ["python", "scripts/process_memory_check.py"]}
      ],
      "evidence": ["evidence/process-memory.json"]
    }
  ]
}
```

`id` is a stable adapter label. The three labels above are recommended because
they communicate intent, but a mission may use another clearly scoped label for
a different domain. `required` defaults to true. A required gate must have at
least one check and one evidence file; all checks must exit zero and every
evidence path must exist as a regular file. An optional gate still has to be
valid if declared.

The commands are responsible for the semantics. For example, the parity command
must compare source, build, and runtime identities rather than merely checking
that a process is healthy; a user-surface command must use the real supported
host and wait for settled state; a process-memory command must distinguish real
history from fixtures and must not promote one successful trace into a global
rule. Those details belong in the mission adapter so the Skill stays reusable.

## Evidence rules

- Keep observed output, inference, and unknown state separate.
- Use paths relative to the mission directory where possible.
- Do not put credentials, private prompts, or sensitive raw content in the
  ledger or evidence unless the mission explicitly authorizes it.
- A screenshot without interaction/state evidence is insufficient for a dynamic
  surface; a unit test without runtime identity is insufficient for parity; a
  fixture without source provenance is insufficient for historical extraction.
