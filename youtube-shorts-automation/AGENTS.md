# YouTube Shorts Automation — Codex Instructions

## Mission

Implement the system described in `youtube_shorts_automation_codex_plan.md` as a production-minded, restartable YouTube Shorts pipeline. Work phase by phase. Preserve the plan's locked decisions unless the user explicitly changes one.

## Locked invariants

- Content arms: food comparisons, cooking transformations, and fictional/funny dog stories.
- Target output: two Shorts per day in `America/Los_Angeles`.
- GitHub Actions orchestrates work; S3 and DynamoDB are the durable sources of truth.
- Every video requires explicit manual approval before YouTube credentials are available.
- Approved videos upload privately first and are scheduled with YouTube `status.publishAt`.
- Text generation uses OpenAI `gpt-5.6-luna` behind a provider interface.
- Visual generation uses Runway image/video APIs behind provider interfaces.
- FFmpeg produces the final 9:16 MP4 and captions.
- Hard generation budget: $45 per calendar month. A reservation must succeed before a paid request.
- Never weaken approval, idempotency, budget, factual-grounding, or secret-handling controls to make a demo pass.

## Required workflow

1. Read the implementation plan, current repository state, and relevant tests before editing.
2. State which implementation phase and acceptance criteria the task covers.
3. If the task spans more than one plan phase, propose phase boundaries before changing code.
4. Map the smallest affected execution path. Delegate only independent read-only exploration, documentation lookup, or review work.
5. Make the smallest coherent change that satisfies the current phase.
6. Add or update tests in the same change.
7. Run the narrowest relevant checks first, then the repository's full verification command when practical.
8. Summarize changed behavior, evidence, remaining risks, and the next plan phase.

## Authority and external effects

Codex may edit repository files and run local/mock tests. Unless the user explicitly authorizes the exact action, do not:

- deploy AWS infrastructure;
- invoke paid OpenAI or Runway generation;
- upload, schedule, publish, delete, or modify a YouTube video;
- rotate credentials or alter GitHub repository secrets;
- merge a pull request or push directly to a protected branch.

Default all integration tests to fakes, recorded fixtures, local emulators, or provider dry-run modes.

## Architecture rules

- Keep domain logic independent of GitHub Actions, AWS SDK clients, FFmpeg processes, and provider SDKs.
- Place external systems behind typed interfaces and inject them into application services.
- Model workflow steps as idempotent state transitions with conditional writes.
- Use deterministic idempotency keys for generation requests, publication slots, uploads, and analytics collections.
- Treat GitHub workflow retries, duplicate events, and out-of-order events as normal.
- Keep raw provider responses out of the domain model; normalize them at adapter boundaries.
- Validate structured model output before any media generation begins.
- Record cost reservations, actual costs, provider request IDs, and artifact hashes.
- Use UTC internally. Convert to `America/Los_Angeles` only at scheduling and presentation boundaries.

## Publishing safety

- The production publishing job must require a manually supplied `draft_id` and a protected GitHub Environment approval.
- The publishing job must reject drafts that are not in the exact approved state.
- Re-check media hash, title, description, audience setting, privacy status, publish time, and budget state immediately before upload.
- Never retry an upload blindly after an ambiguous response. Reconcile by idempotency key and YouTube video ID first.
- Keep an immutable approval audit record with approver, timestamp, artifact hash, and requested schedule.

## Content safety

- Food and cooking facts require approved-source citations in the draft record.
- Do not generate medical, health, weight-loss, or pet-care advice in the MVP.
- Dog stories must be clearly fictional or entertainment-oriented and must not depict cruelty or dangerous handling.
- Do not use copyrighted clips, music, logos, celebrity likenesses, or scraped media without documented rights.
- Do not invent nutrition facts. Fail closed when factual grounding is absent or contradictory.

## Secrets and logs

- Never commit credentials, tokens, OAuth refresh tokens, channel IDs, or signed media URLs.
- Provide `.env.example` with variable names and safe placeholders only.
- Redact secrets and authorization headers from logs, exceptions, snapshots, and test fixtures.
- Prefer GitHub OIDC for AWS. Store the YouTube OAuth refresh token only in the protected publishing environment.

## Python and test conventions

- Target Python 3.12 with type annotations on public interfaces.
- Prefer small pure functions and explicit dataclasses or validated models for domain records.
- Freeze time, random seeds, and provider responses in tests.
- Test failure and retry paths, not only happy paths.
- Critical tests include duplicate workflow delivery, duplicate publication slot, approval bypass, stale artifact hash, cost reservation races, and ambiguous upload recovery.
- Follow the repository's existing formatter, linter, type-checker, and test commands. If none exist yet, establish Ruff, mypy, and pytest in Phase 0 and document a single `make verify` entry point.

## GitHub Actions conventions

- Pin third-party actions to immutable commit SHAs in production workflows.
- Grant the minimum `permissions` per job.
- Use `concurrency` keys for each draft, publication slot, and reconciliation scope.
- Put paid or publishing credentials only on the job that needs them.
- Upload previews as private artifacts with 14-day retention; never expose S3 objects publicly.
- Scheduled workflows must be safe if delayed or replayed.

## Multi-agent policy

- Use `code_mapper` for read-only execution-path mapping.
- Use `api_researcher` to verify current provider/API behavior from primary documentation.
- Use `release_guard` after changes that touch budgets, approvals, credentials, persistence, workflows, or publishing.
- The primary agent owns all edits. Do not run multiple write-capable agents against the same worktree.
- Ask agents for evidence with file paths, symbols, and test gaps; do not accept generic summaries.

## Completion standard

A task is complete only when its behavior is implemented, relevant tests pass, dangerous external effects remain gated, documentation is updated when contracts change, and the result is mapped back to the plan's acceptance criteria.
