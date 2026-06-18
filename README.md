# dogbench

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
```

Requires: collar, and optionally Claude Code / Codex CLI for comparison.

## Usage

```bash
dogbench                          # quick benchmark (built-in task)
dogbench "your custom task"       # custom prompt
dogbench --all                    # compare all installed agents
dogbench --compare hermes         # compare against Hermes upstream
dogbench --model deepseek-v4-pro  # use a specific model
```

## How It Works

1. Detects which agents are installed
2. Runs the same task through each
3. Reads official usage logs (CodexBar, collar sessions, official CLIs)
4. Outputs a clean comparison table with savings

No estimates. No bias. Your own machine, your own tokens.
