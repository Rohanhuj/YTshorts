# YouTube Shorts Automation

A production-minded, restartable pipeline for two manually approved YouTube Shorts per day
across food comparisons, cooking transformations, and fictional/funny dog stories.

## Current implementation

Phases 0 and 1 establish validated domain contracts, deterministic mock providers, styled ASS
caption generation, local FFmpeg fixture rendering, and strict FFprobe media validation. The
test suite renders one 24-second fixture Short for every content arm without paid calls, AWS
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

The media integration tests generate temporary, silent 720x1280 H.264 MP4 files with burned-in
captions for food, cooking, and dog drafts. Files are discarded after the tests; no generated
binary media is committed.

## Next phase

Phase 2 will add S3 and DynamoDB adapters, conditional job and publication-slot reservations,
CloudFormation infrastructure, and GitHub OIDC documentation without deploying resources.
