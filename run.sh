#!/usr/bin/env bash
# Benchmark: collar vs Claude Code vs Codex — token usage for identical task
# Requires: collar, claude, codex, CodexBar (brew install --cask codexbar)
# Usage:   bash scripts/benchmark-agents.sh

set -e

TASK_PROMPT="Write a Python script that:
1. Reads a CSV file of sales data (create sample data if none exists)
2. Groups by product category and calculates total revenue per category
3. Outputs a sorted report to sales_report.txt
4. Writes unit tests for the grouping logic
5. Runs the tests and confirms they pass

Use only standard library modules. Write all files to ./benchmark_output/"

OUTDIR="./benchmark_output"
mkdir -p "$OUTDIR"

echo "=== Collar Benchmark ==="
START=$(date +%s)
collar chat -q "$TASK_PROMPT" --model gpt-5 2>&1
END=$(date +%s)
echo "Collar wall time: $((END - START))s"
sleep 2  # let CodexBar capture

echo ""
echo "=== Claude Code Benchmark ==="
START=$(date +%s)
claude "$TASK_PROMPT" --print --output-format text 2>&1
END=$(date +%s)
echo "Claude Code wall time: $((END - START))s"
sleep 2

echo ""
echo "=== OpenAI Codex Benchmark ==="
START=$(date +%s)
codex exec "$TASK_PROMPT" 2>&1
END=$(date +%s)
echo "Codex wall time: $((END - START))s"

echo ""
echo "=== Results ==="
echo "Check CodexBar menu bar for token counts."
echo "Raw logs at:"
echo "  Collar:   ~/.dag/sessions/"
echo "  Claude:   ~/Library/Application Support/Claude/usage/"
echo "  Codex:    ~/.codex/usage/"
echo ""
echo "Run: cat ~/Library/Application\ Support/Claude/usage/*.jsonl | jq -s 'map(.usage.total_tokens) | add'"
echo "Run: cat ~/.codex/usage/*.jsonl | jq -s 'map(.usage.total_tokens) | add'"
