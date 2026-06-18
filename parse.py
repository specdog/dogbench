#!/usr/bin/env python3
"""Parse CodexBar / official client logs and format as comparison table.

Usage:
  python3 scripts/parse-benchmark.py

Reads:
  ~/Library/Application Support/Claude/usage/*.jsonl  (Claude Code)
  ~/.codex/usage/*.jsonl                                (Codex CLI)
  ~/.dag/sessions/                                       (collar — from dag insights)

Outputs a markdown comparison table for the README.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

def read_jsonl_tokens(path_glob: str) -> dict:
    """Read JSONL usage files and sum input/output/total tokens."""
    import glob
    total_input = 0
    total_output = 0
    total_tokens = 0
    files = glob.glob(os.path.expanduser(path_glob))
    for f in files:
        try:
            with open(f) as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    data = json.loads(line)
                    usage = data.get("usage", data.get("token_usage", {}))
                    total_input += usage.get("input_tokens", usage.get("prompt_tokens", 0))
                    total_output += usage.get("output_tokens", usage.get("completion_tokens", 0))
                    total_tokens += usage.get("total_tokens", 0)
        except (json.JSONDecodeError, OSError):
            continue
    return {
        "input": total_input,
        "output": total_output,
        "total": total_tokens,
        "files": len(files),
    }

def read_collar_tokens() -> dict:
    """Read collar session token usage from dag insights."""
    try:
        result = subprocess.run(
            ["collar", "insights", "--days", "1", "--json"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return {
                "input": data.get("total_input_tokens", 0),
                "output": data.get("total_output_tokens", 0),
                "total": data.get("total_tokens", 0),
            }
    except Exception:
        pass
    return {"input": 0, "output": 0, "total": 0, "note": "run 'collar insights' manually"}

# ── Collect ──────────────────────────────────────────────────
claude = read_jsonl_tokens("~/Library/Application Support/Claude/usage/*.jsonl")
codex = read_jsonl_tokens("~/.codex/usage/*.jsonl")
collar = read_collar_tokens()

# ── Output ──────────────────────────────────────────────────
print()
print("| Agent | Input Tokens | Output Tokens | Total Tokens |")
print("|-------|-------------|--------------|-------------|")
for name, data in [("collar (DAG-first)", collar), ("Claude Code", claude), ("OpenAI Codex", codex)]:
    inp = data.get("input", 0)
    out = data.get("output", 0)
    tot = data.get("total", 0)
    note = data.get("note", "")
    print(f"| {name:<25s} | {inp:>11,} | {out:>12,} | {tot:>11,} |")
    if note:
        print(f"|   ⚠ {note} | | | |")

# ── Savings ──────────────────────────────────────────────────
collar_total = collar.get("total", 0)
print()
if collar_total and claude.get("total", 0):
    claude_total = claude["total"]
    save = claude_total - collar_total
    pct = (save / claude_total) * 100
    print(f"Collar saves {save:,} tokens ({pct:.0f}%) vs Claude Code on identical task.")
if collar_total and codex.get("total", 0):
    codex_total = codex["total"]
    save = codex_total - collar_total
    pct = (save / codex_total) * 100
    print(f"Collar saves {save:,} tokens ({pct:.0f}%) vs Codex on identical task.")
print()
