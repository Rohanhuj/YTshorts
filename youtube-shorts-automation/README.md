# YouTube Shorts Automation

A production-minded, restartable pipeline for two manually approved YouTube Shorts per day
across food comparisons, cooking transformations, and fictional/funny dog stories.

## Current implementation

Phase 0 establishes validated domain contracts, centralized state transitions, configuration,
provider ports, deterministic mock providers, tests, and CI. It performs no paid calls, AWS
deployment, or YouTube upload.

## Local setup

Requirements: Python 3.12, `uv`, FFmpeg, and FFprobe.

```bash
uv sync --locked --group dev
cp .env.example .env
make verify
uv run shorts-automation validate-mocks
```

The `.env` file is ignored by Git. Phase 0 does not require you to fill it in; keep
`MOCK_MODE=true` and `PUBLISHING_ENABLED=false`.

## Safety boundaries

- Every production video requires an independent manual approval workflow.
- Production publishing defaults off.
- Paid provider, AWS, and YouTube integrations remain behind typed interfaces.
- Never place credentials in configuration YAML, source code, fixtures, logs, or workflow files.
- No infrastructure deployment or external provider call is performed by `make verify`.

## Verification

`make verify` runs formatting checks, linting, strict type checks, tests with branch coverage,
a repository secret scan, and a deterministic local FFmpeg smoke render.

## Next phase

Phase 1 will implement deterministic captions, video assembly, FFprobe validation, and one
fixture MP4 for each content arm.
