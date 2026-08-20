---
name: audit-shorts-release
description: Audit changes to the YouTube Shorts automation project for production safety. Use when reviewing GitHub Actions, AWS, DynamoDB, S3, OAuth, YouTube uploads or scheduling, provider calls, budget enforcement, idempotency, approval controls, or a production-readiness milestone. Produces severity-ranked findings and required verification without editing code.
---

# Audit Shorts Release

Review the change without modifying files or performing external actions.

## Audit order

1. Approval: prove no scheduled or untrusted job can reach YouTube credentials or approve its own artifact.
2. Identity: prove the approved media hash, draft ID, publication slot, and uploaded video ID remain linked.
3. Idempotency: replay each workflow mentally and identify ambiguous retries or duplicate side effects.
4. State: verify every transition uses an allowed source state and a conditional write.
5. Budget: verify atomic reservation before paid work, reconciliation afterward, and a hard monthly stop at $45.
6. Secrets: inspect logs, artifacts, exceptions, workflow permissions, OAuth storage, and signed URLs.
7. Media: verify private storage, rights metadata, FFprobe gates, captions, and artifact retention.
8. Content: verify fact citations for food/cooking and safety exclusions for health and pet-care advice.
9. Recovery: verify reconciliation for delayed schedules, partial AWS writes, provider timeouts, and unknown YouTube upload outcomes.
10. Tests: require executable tests for each material failure scenario.

## Output

Return findings first, ordered critical to low. Each finding must include the affected file or symbol, failure scenario, impact, and smallest remediation. Then list test gaps, assumptions requiring primary-documentation verification, and an explicit release recommendation: block, conditional pass, or pass.
