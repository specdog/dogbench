# dogbench

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
git clone https://github.com/specdog/dogbench.git
cd dogbench
pip install -e .
npm install -g dotdog          # for .dag output
```

Requires: collar, and optionally Claude Code / Codex CLI for comparison.

## Usage

```bash
dogbench                          # quick benchmark (built-in task)
dogbench "your custom task"       # custom prompt
dogbench --all                    # compare all installed agents
dogbench --model deepseek-v4-pro  # use a specific model
dogbench --json                   # machine-readable JSON output
dogbench --dag                    # .dag output (collar native)
```

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
# Generate and share
./dogbench --all --json > results.json
cat results.json | curl -X POST https://dogbench.specdog.dev/submit  # coming soon

# Or just tweet a screenshot
./dogbench --all  # post the output
```

## Verify

```bash
# Quick test (collar only, no comparison)
./dogbench "hi"
# Full test (all installed agents)
./dogbench --all --json
```
