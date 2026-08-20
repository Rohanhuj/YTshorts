---
name: implement-shorts-phase
description: Implement one bounded phase or acceptance criterion from the YouTube Shorts automation Codex plan. Use when asked to start, continue, build, or finish a numbered project phase, workflow, adapter, domain contract, or test milestone. Enforces plan traceability, one-writer coordination, mock-first integrations, and phase-specific verification.
---

# Implement Shorts Phase

Implement exactly one coherent slice of `youtube_shorts_automation_codex_plan.md`.

## Procedure

1. Read the relevant plan phase, success criteria, repository instructions, and current code.
2. State the phase, acceptance criteria, exclusions, and external effects before editing.
3. Ask `code_mapper` to map the affected path when more than three modules or a workflow boundary are involved.
4. Ask `api_researcher` to verify any version-sensitive external contract before coding against it.
5. Define or update the domain contract and tests before wiring provider-specific behavior.
6. Implement the smallest end-to-end vertical slice using dependency injection and deterministic fakes.
7. Preserve manual approval, cost reservation, state-transition, and idempotency invariants.
8. Run targeted checks followed by the repository verification command.
9. Ask `release_guard` to audit changes involving paid calls, secrets, AWS, GitHub Actions, persistence, or YouTube.
10. Report acceptance criteria satisfied, commands run, evidence, deferred work, and the next phase.

## Stop conditions

Stop and ask the user before deploying, making a paid generation request, using production credentials, uploading to YouTube, or changing a locked product decision.

If an external contract is unclear, add a typed port and a fake implementation; do not guess the live adapter behavior.
