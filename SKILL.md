---
name: long-mission
description: Use when the user explicitly asks for long-mission/long-task execution or asks for a durable long-task ledger and completion gate; do not use for ordinary short tasks.
---

# Long Mission

This skill turns a long task into a durable mission with an explicit contract, append-only progress ledger, independent acceptance gate, stall detector, and resumable continuation prompt. It is a control loop, not a promise that the host process will run after it exits.

## Invocation boundary

Use this Skill only when the user explicitly requests it (for example, “use long-mission”, “用长任务 Skill”, or “建立长任务验收账本”) or explicitly asks for a durable mission ledger/completion gate. Do not invoke it merely because a task has several steps, multiple files, or tests. For ordinary bounded implementation, debugging, explanation, translation, or one-off UI changes, use the task-appropriate workflow directly; adding a mission ledger would spend unnecessary time and tokens.

If the user explicitly asks for uninterrupted execution but does not mention long-mission, first determine whether the task genuinely needs a durable ledger. Do not silently activate this Skill for a simple task. If a long mission is clearly needed but the user did not request the Skill, keep the normal workflow and state the limitation rather than adding the full ledger automatically.

## Start immediately

Start with the readiness gate. It asks only the missing questions that determine scope, deliverables, completion evidence, confirmation boundaries, and stop limits:

```bash
python3 ~/.agents/skills/long-mission/scripts/mission_start.py .long-mission/<slug>
```

For automation or when the contract is already explicit, pass the fields as flags and use `--non-interactive`. Do not ask questions whose answers are already unambiguous in the current request.

The five question classes are: desired outcome, required artifacts, observable done checks, exclusions/confirmation boundaries, and time/iteration/cost limits. This is an alignment gate, not a request to approve every implementation detail.

When the task includes a reference image, screenshot, mockup, or “make it look like this”, initialize the mission with `--profile reference_ui`. This activates a reference contract, a minimal feasibility probe, capability-ceiling detection, and a visual/interaction acceptance gate. A reference image is not an executable specification until its structure, relationships, interactions, responsive states, and allowed deviations are recorded in the mission adapter.

The readiness gate then creates a mission before substantial work:

```bash
python3 ~/.agents/skills/long-mission/scripts/mission_init.py \
  .long-mission/<slug> --objective "..." \
  --deliverable path/to/output --acceptance "tests pass"
```

Read `MISSION.md`, `state.json`, and `PROGRESS.md`. Keep the current objective, scope, exclusions, deliverables, acceptance checks, blockers, and next action there—not only in chat context.

## PRD execution mode

When the mission is executing a PRD, do not treat every sentence in the PRD as the same kind of requirement. Before implementation, create a PRD interpretation with four buckets:

| Bucket | Meaning | Default treatment |
| --- | --- | --- |
| Outcome goals | What the product or user must gain | Hard acceptance |
| Invariants/constraints | Compatibility, safety, data semantics, public API, non-regression, explicit user decisions | Hard constraint |
| Implementation proposals | Suggested framework, renderer, file layout, algorithm, or sequence | Soft route hint; may be replaced with evidence |
| Examples/open decisions | Illustrations, alternatives, TBDs, or unresolved trade-offs | Explore or ask when material |

Words such as “must”, “shall”, “required”, or an explicitly approved technology choice are binding unless they are impossible, unsafe, or contradicted by a higher-priority current user instruction. Words such as “prefer”, “recommended”, “for example”, or “could use” are not a route lock. If the PRD is ambiguous, preserve the outcome, record the ambiguity, and either run a bounded probe or ask one focused question before a material irreversible choice.

The PRD remains the source of intended outcomes; evidence remains the source of what actually works. If the proposed route fails a critical outcome, use the replan protocol, explain the deviation, and keep the original outcome and compatibility constraints in the acceptance contract. Do not silently rewrite the PRD to make a failed route look successful.

## Outcome contract, not an implementation rail

The mission contract constrains **outcomes and invariants**, not the first implementation idea. A plan is a hypothesis that may be replaced when evidence shows that another route is better.

Keep these separate:

- **Hard invariants:** user goal, authorization/safety boundaries, source-of-truth rules, non-regression requirements, evidence/data semantics, and critical acceptance outcomes.
- **Soft strategy:** framework, renderer, component decomposition, query plan, fallback route, number of intermediate experiments, and the order of implementation steps.

For UI and reference-driven work, “match the reference” means preserve required structure, relationships, interaction, evidence semantics, and responsive behavior. It does not require a particular rendering library, DOM shape, coordinate set, or styling technique.

### Exploration window

Before committing to a costly implementation, use a bounded exploration window (the default mission adapter may allocate up to three probes). A probe is a small, falsifiable experiment against the hardest requirement: for example, whether an edge renderer is actually visible in a real screenshot, whether a receipt projection preserves parent/child counts, or whether a deployed bundle contains the current source revision.

Record each probe with:

```text
hypothesis → route attempted → independent evidence → measured result → decision
```

Exploration is not an excuse to avoid delivery. Once the evidence selects a route, close the exploration window and implement. If the selected route fails a critical invariant, reopen the window instead of polishing the same approach indefinitely.

### Replanning protocol

An agent may replace the plan when any of these occur:

- two materially different attempts do not improve the named defect;
- DOM/API state is correct but the real user surface is wrong;
- parent and child receipts disagree;
- the source/build/runtime identity is not the same;
- the chosen engine cannot express a critical reference requirement;
- the solution is accumulating special-case patches instead of reducing risk.

Before changing route, append a `replan` entry to `PROGRESS.md` and `state.json` containing the superseded hypothesis, observed failure, new route, preserved invariants, and the next falsifiable check. Replanning is a first-class success behavior, not a failure of obedience.

Use the helper when available:

```bash
python3 ~/.agents/skills/long-mission/scripts/mission_replan.py <mission-dir> \
  --superseded "..." --observed-failure "..." --new-route "..." \
  --preserve "critical invariant" --next-action "..."
```

Use `plan.status = hypothesis|selected|superseded` and increment `plan.version`. Keep task-specific routes in the mission adapter; never add them to this Skill.

## Non-negotiable loop

1. Choose one bounded next action from `state.json`.
2. Execute it and capture concrete evidence (file, command, test output, screenshot, or API receipt).
3. Append the result and next action to `PROGRESS.md`; update `state.json` atomically.
4. Run the independent gate:
   `python3 .../acceptance_gate.py <mission-dir>`.
5. If it fails, diagnose the listed gap and continue. Never convert a failing gate into “done”.
6. Run `stall_detector.py`; after repeated no-progress iterations, change strategy or record a real blocker.

For `reference_ui` and `capability_sensitive` missions, also run `reference_gate.py`. A pending capability probe, an empty acceptance matrix, an unrecorded degraded result, or a critical item marked degraded/blocked cannot pass the gate.

Only report **complete** after the gate exits 0 and the evidence is present. To prevent a stale or hand-edited status, close the mission through:

```bash
python3 ~/.agents/skills/long-mission/scripts/mission_close.py <mission-dir>
```

`mission_close.py` is the only normal path that writes `status=complete`; it records a completion receipt after the independent gate passes. A timeout, quota limit, unavailable external service, missing user decision, or safety boundary is `blocked`/`paused`/`incomplete`, never success. Do not invent background progress after the process ends.

Every mission must also have `MISSION-REPORT.md`. Create its English-first/Chinese-following template with:

```bash
python3 ~/.agents/skills/long-mission/scripts/mission_report.py <mission-dir>
```

The final report must describe the objective and outcome, hard acceptance contract, exploration and replans, execution evidence, tests/build/runtime checks, failures and deviations, unresolved items, artifacts, and next actions. It is a concise final audit narrative, not a dump of private chain-of-thought. The independent gate checks that both `## English` and `## 中文` sections exist before completion.

### Mission overlap guard

Before creating a new mission, inspect active and recently completed missions for overlapping deliverables. If two missions modify the same core files or the same user-visible surface, continue the existing mission or create an explicit follow-up with inherited acceptance evidence. Do not let parallel missions each claim completion against different contracts.

## Evidence and safety

- Separate observed, inferred, and unknown results.
- A model's self-report is not verification; require an independent command or artifact check.
- A reference-driven task must first run a minimal feasibility probe against the hardest representative requirements. Record each attempt with a falsifiable hypothesis, implementation route, measured result, and whether the result improved. Do not spend the whole mission polishing a target the current engine cannot express.
- Distinguish `native_pass`, `workaround_pass`, `degraded_pass`, `blocked_engine`, `blocked_missing_input`, and `needs_user_decision`. A capability ceiling is a valid finding, not permission to claim completion.
- If two or more materially different attempts produce no measurable improvement, invoke the capability stall rule: change renderer/strategy, use an explicitly allowed fallback, or record the bottleneck and stop as blocked. Never hide an engine limitation behind a visual similarity score.
- Reference acceptance has separate categories: structure, relationship/topology, interaction, visual, evidence/data, responsive, and accessibility. Critical structure, interaction, and evidence failures veto completion; decorative animation, shadow, or gradient may be degraded only when the mission contract says so.
- Make the distinction explicit in the adapter: **hard acceptance** describes outcomes that must hold; **soft preferences** describe a desired look or first implementation. An agent may change the engine, renderer, layout strategy, data projection, or component structure when that improves a hard outcome. Do not turn a reference screenshot, first plan, or chosen library into a hidden hard constraint.
- Keep reference-specific nodes, colors, page names, engines, and thresholds in the mission adapter (`reference-contract.json`, `capability-probe.json`, `acceptance-matrix.json`), never in this Skill. This preserves generalization.
- Keep secrets out of `MISSION.md`, logs, prompts, and commits.
- Do not delete broad paths, force-push, publish, or send external messages without explicit authorization.
- If a memory system is available, use its task/process-memory adapter only for conditional hints and prior failure patterns. A local search is not automatically a memory receipt; the adapter must report source, scope, and delivery state.

## Generalization boundary

This Skill is intentionally domain-agnostic. It defines invariants, not solutions:

- The Skill layer contains the control protocol: contract, evidence, independent gate, bounded continuation, safety boundary, and recovery.
- The mission layer contains task-specific paths, files, commands, locale rules, acceptance thresholds, and known exceptions.
- The process-memory layer may retain a reusable pattern only after repeated evidence across suitable tasks; every pattern needs applicability conditions, counterexamples, confidence, validation time, and expiry/revalidation rules.

Do not add a one-off bug fix, UI label, repository path, provider name, model name, or fixed timeout to this Skill. Put it in the current mission adapter or process memory. When a new issue appears, first ask whether it is a cross-domain invariant; if not, keep it local. When a pattern is promoted, test it on a different task shape before making it reusable.

For user-facing systems, the mission adapter should audit three separate surfaces: static UI text, runtime-generated UI text, and user/content data. The first two must satisfy the active locale; the third must retain its source language unless translation is explicitly part of the task. Never use a whole-page “contains foreign characters” check as the only acceptance test.

## Three conditional completion gates

The mission adapter may declare one or more of these gates in `state.json` under
`verification_gates`. They are conditional, not a reason to add work to every
mission. The Skill defines the invariant; the adapter supplies commands,
selectors, paths, and task-specific thresholds. See
`references/acceptance-contract.md` for the schema.

### Real user-surface gate

Declare `id: "real_user_surface"` when the task changes a UI, browser flow,
desktop surface, or any interaction whose correctness cannot be established by
static markup alone. The gate must use an actual supported host after a fresh
load, wait for asynchronous settling, exercise at least one representative
interaction, and save independently inspectable evidence (for example a
screenshot plus accessibility/DOM or event evidence). A headless/unit check may
supplement this gate but cannot replace it. Re-read the surface after navigation,
selection, scrolling, resizing, or async refresh; do not treat a stale capture as
current state.

When a UI projects receipts, counters, or route status, declare a separate
`receipt_projection` check in the mission adapter. Exercise at least
`no_call`, `called_empty`, `preference_only`, `history_only`, and `mixed` fixtures
(or the task's equivalent). Assert that parent aggregates are not copied into
child nodes and that `unknown`/`not_measured` are not rendered as numeric zero.

### Source/build/runtime parity gate

Declare `id: "artifact_parity"` when source, generated artifacts, a deployed
bundle, or a running service can drift apart. The adapter must provide an
independent command that records or compares the relevant source, build, and
runtime identity (revision, digest, timestamp, or equivalent) and fails on
mismatch. Do not infer parity from a successful build or a server health check
alone. Paths and commands stay in the adapter; this Skill never assumes a
repository layout, framework, port, provider, or release mechanism.

### Conditional process-memory gate

Declare `id: "process_memory"` only when the task includes multi-step failures
and recoveries, learning/process-memory behavior, or an explicit request to
retain execution experience. The evidence must distinguish the observed
trajectory from a derived episode/pattern/skill candidate, show its source and
applicability, and verify retrieval or delivery independently when that is part
of the requirement. Fixture-only checks must be labelled as fixture evidence;
they cannot be reported as a real historical extraction. A single successful
run never promotes a global reusable rule: promotion requires the adapter's
specified repeated evidence, counterexamples, confidence, and revalidation
policy.

For every declared gate, completion requires its checks to pass and its evidence
files to exist. If a gate is not applicable, omit it rather than marking a
meaningful check as passed without running it. This keeps the protocol
generalizable while preventing a static or fixture-only completion claim.

## Resume after compaction or interruption

```bash
python3 ~/.agents/skills/long-mission/scripts/continuation_prompt.py <mission-dir>
```

Resume from the ledger, not from an imagined prior turn. If the host supports an outer runner, feed this prompt into the next iteration and cap iterations, time, and cost. If no runner is present, the ledger still makes the next turn deterministic and auditable.

### Preventing premature turn completion

The Skill cannot keep a host process alive by itself. When the current turn ends, only an outer runner, automation, or a new continuation turn can continue the work. Therefore:

- never send a success-style final response while the gate is failing or a required action remains;
- write the next action and the unresolved gate failure to the ledger;
- use `continuation_prompt.py` for the next turn, or `mission_runner.py` when the host explicitly supports bounded autonomous iterations;
- treat an iteration limit as `incomplete`, not as success;
- make the final response say whether the result is `complete`, `incomplete`, `blocked`, or `needs_user_decision`.

Autonomy is preserved inside the exploration window; persistence is provided by the ledger/runner. They solve different problems and should not be confused.

## Quick status

```bash
python3 ~/.agents/skills/long-mission/scripts/stall_detector.py <mission-dir>
python3 ~/.agents/skills/long-mission/scripts/acceptance_gate.py <mission-dir>
```

For a host that can run an outer command loop, `mission_runner.py` accepts a command template containing `{prompt}`. It is bounded by `max_iterations`, stores each stdout/stderr transcript under `runs/`, and delegates completion to the gate. Run `guard_command.py` on proposed argv before allowing a mutating command. This wrapper is an adapter, not a hidden background service and not a bypass of Codex permissions.

The skill deliberately does not override human approval, security policy, or tool availability; those boundaries are explicit mission states.

## Reference-driven mission protocol

Use this protocol when a screenshot or generated image is the target.

1. **Probe before building.** Render a minimal slice containing the hardest structural and interactive requirements. Verify the actual browser/renderer, not a mock DOM.
2. **Classify each requirement.** Mark it `native`, `workaround`, `degradable`, or `blocked`; record evidence and the next fallback.
3. **Separate semantics from appearance.** A graph can look similar while its edges, receipts, or source provenance are wrong. Require topology/data assertions and screenshots.
4. **Measure improvement.** Every iteration must reduce a named defect or improve a named metric. Repeated cosmetic edits without metric movement are a stall.
5. **Fallback deliberately.** Prefer a different rendering strategy before repeated parameter tweaking. A fallback must preserve all critical requirements.
6. **Stop honestly.** If the engine ceiling blocks a critical requirement, set `capability_probe.status=blocked_engine`, record the bottleneck and attempted routes, and leave the mission incomplete/blocked. If only non-critical details are affected, set `degraded_pass` and document every deviation.

The independent checks are:

```bash
python3 ~/.agents/skills/long-mission/scripts/reference_gate.py .long-mission/<slug>
python3 ~/.agents/skills/long-mission/scripts/stall_detector.py .long-mission/<slug>
```
