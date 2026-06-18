# dogbench

[![semver](https://img.shields.io/badge/semver-0.1.0-blue)](https://semver.org)
[![benchmark](https://img.shields.io/badge/live%20results-specdog.github.io/dogbench-green)](https://specdog.github.io/dogbench/)

One command to prove collar saves tokens.

```bash
dogbench
```

Output:
```
╔══════════════════════════════════════════╗
║        dogbench — token benchmark        ║
╚══════════════════════════════════════════╝

  ┌──────────────────────┬──────────┬───────────┬──────────┐
  │ Agent                │  Input   │  Output   │   Cost   │
  ├──────────────────────┼──────────┼───────────┼──────────┤
  │ collar (DAG-first)   │    1,234 │       567 │ $0.0072  │
  │ Claude Code          │    3,456 │     1,200 │ $0.0284  │
  │ OpenAI Codex         │    2,890 │       980 │ $0.0221  │
  └──────────────────────┴──────────┴───────────┴──────────┘

  ✓ collar saved 2,855 tokens (55%) vs Claude Code
    That's $0.0212 saved on this task alone.
```

## Install

```bash
# Clone (or pull if already cloned)
git clone https://github.com/specdog/dogbench.git 2>/dev/null || (cd dogbench && git pull origin feat/init)
cd dogbench

# Install (use collar's venv if you have it)
pip install -e . 2>/dev/null || ~/collar/.venv/bin/pip install -e .

# Dotdog (skip if already installed)
which dotdog || npm install -g dotdog
```

No conflicts. Works on fresh installs and existing setups.

Requires: collar, and optionally Claude Code / Codex CLI for comparison.

## One-Liner

```bash
cd ~/dogbench && git pull origin feat/init && ~/collar/.venv/bin/pip install -e . && ./dogbench --all --json
```

## Usage

| Setup | Command |
|-------|---------|
| Collar only | `./dogbench --json` |
| Collar + Claude Code | `./dogbench --all --json` |
| Collar + Codex | `./dogbench --all --json` |
| Collar + Hermes | `./dogbench --compare hermes --json` |
| DeepSeek backend | `./dogbench --model deepseek-v4-pro --json` |
| Claude backend | `./dogbench --model claude-sonnet-4 --json` |
| GPT-5 backend | `./dogbench --model gpt-5 --json` |
| Custom task | `dogbench "your prompt" --json` |
| .dag output | `dogbench --dag` |

## Comparison Scenarios

```bash
# Same harness, different engines — proves DAG savings are architectural
dogbench --compare claude --model gpt-5
dogbench --compare codex --model gpt-5

# Same engine, different harnesses — raw collar vs raw Claude Code
dogbench --compare claude codex --model claude-sonnet-4

# Collar + DeepSeek vs Collar + Codex (same harness, different backends)
collar chat -q "your task" --model deepseek-v4-pro
mv ~/.dag/sessions/ ~/.dag/sessions_backup
collar chat -q "your task" --model gpt-5
# Compare the two session directories
```

## Output Formats

| Flag | Format | Use |
|------|--------|-----|
| (none) | Text table | Human readable |
| `--json` | JSON | CI/CD, scripts |
| `--dag` | .dag file | Collar native reading |

JSON output includes per-agent token counts, wall time, and cost in USD.

## How It Works

1. Detects which agents are installed
2. Runs the same task through each
3. Reads official usage logs (CodexBar, collar sessions, official CLIs)
4. Outputs a clean comparison table with savings

No estimates. No bias. Your own machine, your own tokens.

## Add Your Own Agent

Edit `agents.yaml`:

```yaml
agents:
  my-agent:
    name: "My Agent"
    command: 'my-agent-cli "{prompt}"'
    log_type: jsonl
    log_path: "~/path/to/usage/*.jsonl"
    log_key: "usage.total_tokens"
```

PRs welcome. Any CLI tool that accepts a prompt and writes usage logs can be benchmarked.

## Share Your Results

```bash
# Run benchmark
./dogbench --all --json > results.json

# Submit via PR (preferred)
git checkout -b results/yourname
git add results.json
git commit -m "results: add benchmark data"
git push origin results/yourname
# Open a PR at https://github.com/specdog/dogbench

# Or post to an issue
open https://github.com/specdog/dogbench/issues/new
```

## Verify

```bash
# Quick test (collar only, no comparison)
./dogbench "hi"
# Full test (all installed agents)
./dogbench --all --json
```
