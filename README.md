# fastc

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![uv](https://img.shields.io/badge/uv-script-blueviolet.svg)](https://docs.astral.sh/uv/)

Zero-config CLI tool that analyses your git diff with an LLM and creates atomic, conventional commits.

```
$ fastc
✓ Staged 12 files
✓ Planned 3 commits

  Planned commits:
  ──────────────────────────────────────────────────────────
   1  feat(auth): add JWT token validation
       src/auth.go, src/auth_test.go
   2  refactor(db): extract connection pool config
       src/db.go, src/config.go +2 more
   3  chore: update lockfiles
       go.sum
  ──────────────────────────────────────────────────────────

✓ feat(auth): add JWT token validation
✓ refactor(db): extract connection pool config
✓ chore: update lockfiles
✓ Pushed
```

## Features

- **Atomic commits** - Groups related changes into logical commits
- **Conventional commit format** - `feat`, `fix`, `refactor`, `chore`, `docs`, `style`, `test`, `perf`
- **Smart diff handling** - Two-phase approach for large diffs (15+ files)
- **Lockfile separation** - Commits lockfiles separately with `chore: update lockfiles`
- **Diff compression** - Reduces token usage for large diffs while preserving context
- **Retry with backoff** - Automatic retry on API rate limits or transient errors
- **Rename detection** - Properly handles renamed files

## Install

Requires [uv](https://docs.astral.sh/uv/getting-started/installation/).

```bash
# Clone and symlink (use absolute path)
git clone https://github.com/danwt/demo-fast-commit.git
cd demo-fast-commit && ln -s "$(pwd)/fc" ~/.local/bin/fastc && cd ..

# Create config
mkdir -p ~/.config/fast-commit
cat > ~/.config/fast-commit/.env << 'EOF'
OPENROUTER_API_KEY=sk-or-v1-your-key-here
MODEL=google/gemini-2.0-flash-001
EOF
```

Get an API key from [openrouter.ai/keys](https://openrouter.ai/keys).

## Usage

```bash
cd your-git-repo
fastc                # analyse, commit, and push
fastc --dry-run      # preview commits without executing
fastc --no-push      # commit but don't push
fastc --no-verify    # bypass pre-commit hooks
fastc --bulk         # skip LLM, use smart file tree analysis
fastc --provider claude   # route prompts through the Claude Code CLI
```

The tool will:
- Use staged changes if any exist
- Otherwise stage and commit all changes
- Push after committing (unless `--no-push`)

## Config

`~/.config/fast-commit/.env`:

| Variable | Description |
|----------|-------------|
| `OPENROUTER_API_KEY` | Your OpenRouter API key (required for the default provider) |
| `MODEL` | Model to use (required for the default provider). Any model on OpenRouter works. |
| `STRUCTURED_OUTPUT` | Set to `false` to disable JSON mode (default: `true`) |
| `CLAUDE_MODEL` | Model for `--provider claude` (default: `haiku`) |

## Providers

`fastc` talks to OpenRouter over HTTP. `fastc --provider claude` shells out to the
Claude Code CLI instead, which sends nothing to a third party and needs no API
key, because it spends the Agent SDK credit attached to a Claude subscription.

Install the CLI from [claude.com/code](https://claude.com/code) and log in with
`claude` once. The prompt runs with `--safe-mode`, so repo `CLAUDE.md` files,
skills, plugins, hooks and MCP servers are all ignored.

It is much slower: tens of seconds per request against 2 to 3 for a fast
OpenRouter model. The model thinks before answering, that cannot be turned off
through the CLI, and how long it thinks varies by up to 9x between identical
runs. Each request is also a process holding about 450MB, so phase 2 runs 4 at
a time rather than 32.

To keep the prompt small the claude path strips context lines from the diff,
which cuts it by roughly a quarter, and uses a shorter form of the scope rules.
Phase 2 asks for a subject only when a group holds a single file, and reuses
that group's phase 1 hint as the commit body. Commit messages themselves are
the same shape on both providers.

### Recommended models

| Model | Speed | Quality | Cost |
|-------|-------|---------|------|
| `google/gemini-2.0-flash-001` | Fast | Good | Low |
| `anthropic/claude-3.5-sonnet` | Medium | Excellent | Medium |
| `openai/gpt-4o-mini` | Fast | Good | Low |

## How it works

1. **Detect changes** - Uses staged changes if any, otherwise stages everything
2. **Exclude noise** - Filters out lockfiles and generated files from analysis
3. **Analyse diff** - For small diffs, sends directly to LLM. For large diffs (15+ files), uses two-phase approach:
   - Phase 1: Send file summary to group files by logical change
   - Phase 2: Generate commit message for each group
4. **Create commits** - Stages files per group and commits with generated message
5. **Commit lockfiles** - Any lockfiles get a separate `chore: update lockfiles` commit
6. **Push** - Pushes all commits to remote

### Excluded from analysis

These files are excluded from LLM analysis (but still committed):

- **Lockfiles**: `pnpm-lock.yaml`, `package-lock.json`, `yarn.lock`, `bun.lockb`, `Cargo.lock`, `poetry.lock`, `Pipfile.lock`, `go.sum`, `composer.lock`, `Gemfile.lock`
- **Generated**: `*.min.js`, `*.min.css`, `*.map`

## Testing

```bash
uv run --with pytest pytest test_fc.py -v
```

## Claude Code integration

Copy [`SKILL.md`](SKILL.md) to your `.claude/skills/fastc/` directory:

```bash
mkdir -p ~/.claude/skills/fastc
cp SKILL.md ~/.claude/skills/fastc/SKILL.md
```

Then invoke with `/fastc` in Claude Code.

## License

MIT
