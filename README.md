# dogbench

Real token benchmarks for AI coding agents. No estimates. No bias.

Measures token consumption by running identical tasks through multiple agents and reading official client logs via [CodexBar](https://github.com/steipete/CodexBar).

## Quick Start

```bash
brew install --cask codexbar
pip install collar
bash run.sh "your task prompt"
python3 parse.py
```
