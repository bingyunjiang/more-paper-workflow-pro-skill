# Agent Compatibility

## Shared core

- `SKILL.md` contains the shared description and the canonical skill version.
- `README.md` is public-facing only.
- `agents/step_*.md` and `references/*.md` hold the runtime contracts.

## Thin adapters

- Codex: `agents/openai.yaml`
- Claude Code / Claude plugin: `.claude-plugin/marketplace.json`
- Hermes: native skill install + Markdown entry
- OpenClaw: native skill install + Markdown entry
- Reasonix: Markdown core entry; add a dedicated manifest only if the runtime later requires one

## Compatibility rule

- No agent gets a forked workflow.
- If a platform needs metadata, it gets metadata only.
- If a platform needs an entry hint, it gets an entry hint only.
