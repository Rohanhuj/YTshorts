# Codex Setup for YouTube Shorts Automation

This pack is designed to be copied into the root of the repository that contains `youtube_shorts_automation_codex_plan.md`.

## Included files

| Path | Purpose |
|---|---|
| `AGENTS.md` | Project rules, locked decisions, safety gates, coding conventions, and the implementation workflow Codex reads automatically. |
| `.codex/config.toml` | Safe project defaults, a three-agent concurrency limit, and documentation MCP configuration. |
| `.codex/agents/code-mapper.toml` | Read-only code and workflow mapper. |
| `.codex/agents/api-researcher.toml` | Read-only primary-documentation researcher. |
| `.codex/agents/release-guard.toml` | Read-only publishing, budget, state, and credential auditor. |
| `.agents/skills/implement-shorts-phase/` | Repo-local skill for implementing one plan phase at a time. |
| `.agents/skills/audit-shorts-release/` | Repo-local skill for production-safety reviews. |

## Installation

1. Copy this pack's contents into the project root, preserving hidden directories.
2. Keep `youtube_shorts_automation_codex_plan.md` in the same project root.
3. Review `.codex/config.toml`, then mark the repository trusted in Codex so project-scoped configuration can load.
4. Restart Codex and run `/mcp` or `codex mcp list` to confirm the documentation server.
5. Leave Context7 disabled initially. Enable it only after reviewing the npm package and deciding its additional documentation coverage is worth the tool and network surface.
6. Commit `AGENTS.md`, `.codex/`, and `.agents/skills/` with the application code so the team receives identical behavior.

## Recommended starting prompts

Start Phase 0:

> Use $implement-shorts-phase to implement Phase 0 from `youtube_shorts_automation_codex_plan.md`. Have `code_mapper` inspect the current repository first. Do not deploy or call paid APIs. Stop after tests and a Phase 0 acceptance-criteria report.

Review a branch:

> Review this branch against the implementation plan. Have `code_mapper` trace the changed execution paths and `release_guard` audit publishing, state, credentials, and budget behavior. Return findings before proposing edits.

Verify an external integration:

> Have `api_researcher` verify the current official API behavior needed for this adapter. Use primary documentation only and report exact request fields, authentication, retry semantics, and deprecations before implementation.

## MCP recommendations

Use a small tool surface at first:

- **OpenAI Developer Docs MCP:** included and enabled. It is authoritative for OpenAI model and API implementation details.
- **Context7:** included but disabled. It can help with current third-party library documentation when official sources are fragmented.
- **GitHub MCP:** add later if Codex must create or manage pull requests, issues, or workflow runs. Normal repository implementation only needs `git` and the GitHub CLI.
- **Do not add an AWS control-plane MCP for the MVP.** Terraform, AWS CLI dry runs, least-privilege roles, and explicit deployment authorization give a clearer safety boundary.
- **Do not expose YouTube publishing as an MCP tool.** Keep publishing behind the protected GitHub Actions approval workflow so Codex cannot bypass the product's main safety gate.

## Plugin recommendations

- **GitHub:** useful for inspecting pull requests, reviews, Actions failures, and CI evidence while developing.
- **Codex Security:** use before adding production AWS and YouTube credentials, and again before the controlled launch.
- **vidIQ:** optional for manual trend and title research after the pipeline works; do not let it become a runtime dependency.
- **Runway:** optional for prompt prototyping and visual experiments. The production pipeline should use the documented API through the project's provider adapter.

No project-management or database plugin is needed for the MVP. Adding Airtable, Asana, or Trello would duplicate DynamoDB/GitHub state and make recovery harder.

## Settings rationale

- `approval_policy = "on-request"` and `sandbox_mode = "workspace-write"` allow normal coding while retaining approval boundaries.
- Cached web search reduces exposure to arbitrary live pages; `api_researcher` should use primary sources for version-sensitive contracts.
- Three subagent threads are enough for mapping, research, and safety review without excessive token use.
- Read-only custom agents prevent parallel edits. The primary Codex session is the single writer.
- Do not store credentials in `.codex/config.toml`; use local environment configuration, GitHub Environments, GitHub Secrets, and AWS OIDC as described in the implementation plan.

## Maintenance

Update `AGENTS.md` whenever a locked decision changes. Update a skill when the repeatable workflow changes. Update a custom agent only when its specialist role or tool surface changes. Keep environment-specific credentials and account identifiers out of all three.
