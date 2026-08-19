---
name: fastc
description: Auto-commit git changes using LLM-generated conventional commit messages
user_invocable: true
---

# fastc - Fast LLM-powered git commits

Use this skill when the user wants to quickly commit and push their current git changes using LLM-generated commit messages.

## When to use

- User says "commit this", "push this", "fastc", or similar
- User wants to commit changes without writing commit messages manually
- User wants atomic conventional commits generated from their diff

## How to invoke

```bash
fastc                # analyse, commit, and push
fastc --dry-run      # preview commits without executing
fastc --no-push      # commit but don't push
fastc --no-verify    # bypass pre-commit hooks
fastc --bulk         # skip LLM, use smart file tree analysis
fastc --provider claude   # route prompts through the Claude Code CLI
```

## Prerequisites

- `uv` must be installed
- `~/.config/fast-commit/.env` must exist with `OPENROUTER_API_KEY` and `MODEL` set
- `--provider claude` needs neither of those, but does need the `claude` CLI on PATH and logged in
- The current directory must be a git repo with uncommitted changes

## What it does

1. Detects staged or unstaged changes
2. Excludes lockfiles from analysis (commits them separately)
3. For large diffs (15+ files), uses two-phase grouping approach
4. Sends diff to an LLM, via OpenRouter or the Claude Code CLI
5. Creates atomic commits with conventional commit messages
6. Pushes to the remote

## Troubleshooting

- If it says "nothing to commit", there are no changes in the repo
- If the API returns 401, the OpenRouter key is invalid or has quotes around it
- If pre-commit hooks block the commit, use `--no-verify` to bypass
- Config file: `~/.config/fast-commit/.env`
