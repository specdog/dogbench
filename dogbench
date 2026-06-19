#!/usr/bin/env python3
"""dogbench v3 — spec-required vs self-contained tasks, terminal bench mode"""
import argparse, datetime, json, os, shlex, statistics, subprocess, sys, time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
TMPDIR = Path("/tmp")

AGENTS = {
    "hermes":      ("hermes",              'hermes chat -q {task}',   TMPDIR),
    "hermes_dag":  ("hermes + dotdog",     'hermes chat -q {task}',   TMPDIR),
    "collar":      ("collar",              'collar chat -q {task}',   TMPDIR),
    "collar_dag":  ("collar + dotdog",     'collar chat -q {task}',   TMPDIR),
}

COLORS = {"hermes": "\033[36m", "hermes_dag": "\033[35m", "collar": "\033[33m", "collar_dag": "\033[32m"}
RATES = {"deepseek-v4-pro": {"input": 0.50, "output": 2.00}, "default": {"input": 1.00, "output": 5.00}}

def load_tests():
    tests = []
    for subdir in sorted((SCRIPT_DIR / "tests").iterdir()):
        if not subdir.is_dir(): continue
        tf = subdir / "test.json"
        if tf.exists():
            t = json.loads(tf.read_text())
            tests.append({"id": t["id"], "task": t["task"], "cwd": str(subdir / "sample"), "grader": str(subdir / "grader.py")})
    return tests

def detect_model():
    cfg = Path.home() / ".dag" / "config.yaml"
    if cfg.exists():
        try:
            import yaml
            with open(cfg) as f: d = yaml.safe_load(f) or {}
            m = d.get("model", {})
            if isinstance(m, dict): return m.get("default", "deepseek-v4-pro")
            if isinstance(m, str) and m: return m
        except: pass
    return "deepseek-v4-pro"

def fmt(n): return f"{n:,}" if n else "N/A"
def cost(i, o, m="default"):
    r = RATES.get(m, RATES["default"])
    return (i/1e6)*r["input"] + (o/1e6)*r["output"]

def db_path(aid):
    home = Path.home()
    if aid.startswith("collar"): return home / ".dag" / "state.db"
    if aid.startswith("hermes"): return home / ".hermes" / "state.db"

def read_tokens(aid, sid=None):
    db = db_path(aid)
    if not db or not db.exists(): return (0, 0)
    import sqlite3
    for _ in range(60):
        try:
            conn = sqlite3.connect(str(db))
            if sid: rows = conn.execute("SELECT input_tokens, output_tokens FROM sessions WHERE id=?", (sid,)).fetchall()
            else: rows = conn.execute("SELECT input_tokens, output_tokens FROM sessions ORDER BY started_at DESC LIMIT 1").fetchall()
            conn.close()
            if rows and (rows[0][0] or 0) > 0: return (rows[0][0], rows[0][1] or 0)
        except: pass
        time.sleep(1)
    return (0, 0)

def run_test(aid, name, cmd_tpl, cwd, test):
    task = test["task"]
    cmd = cmd_tpl.replace("{task}", shlex.quote(task))
    try:
        proc = subprocess.run(cmd, shell=True, capture_output=True, timeout=300, cwd=str(cwd))
        sid = None
        for line in (proc.stderr + proc.stdout).decode(errors="replace").splitlines():
            if "Session:" in line:
                sid = line.split("Session:")[-1].strip().split()[0]
                break
        inp, out = read_tokens(aid, sid)
        # Grade
        grader = test.get("grader") or (SCRIPT_DIR / "tests" / "grader.py")
        gr = subprocess.run([sys.executable, str(grader), str(cwd)], capture_output=True, timeout=30)
        passed = json.loads(gr.stdout).get("passed", False) if gr.returncode == 0 else False
        return (inp, out, passed)
    except: return (0, 0, False)

def terminal_bench():
    """Measure raw MCP query cost without running a full agent."""
    print("\n  \033[1mTerminal Bench — raw MCP query cost\033[0m\n")

    serve_cmd = f"bun /Users/dico/dotdog/packages/dotdog/src/cli.ts serve {SCRIPT_DIR} 2>/dev/null"

    def mcp_call(payload):
        p = payload + "\n"
        proc = subprocess.run(
            serve_cmd,
            shell=True, capture_output=True, timeout=10,
            cwd=str(SCRIPT_DIR),
            input=p.encode()
        )
        for line in proc.stdout.decode(errors="replace").splitlines():
            try:
                return json.loads(line)
            except:
                continue
        return None

    # 1. tools/list size
    r = mcp_call('{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"bench","version":"0.1.0"}}}')
    r = mcp_call('{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}')
    if r:
        tools_json = json.dumps(r["result"])
        print(f"  tools/list response: {len(tools_json)} chars, {len(tools_json.split())} words")
        for t in r["result"]["tools"]:
            print(f"    {t['name']}: {t['description']}")

    # 2. getEntity response size
    r = mcp_call('{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"getEntity","arguments":{"name":"dogbench"}}}')
    if r:
        text = r["result"]["content"][0]["text"]
        print(f"\n  getEntity('dogbench'): {len(text)} chars")
        print(f"    {text}")

    # 3. search response size
    r = mcp_call('{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"search","arguments":{"q":"dog"}}}')
    if r:
        text = r["result"]["content"][0]["text"]
        print(f"\n  search('dog'): {len(text)} chars")
        print(f"    {text}")

    # 4. traverse response size
    r = mcp_call('{"jsonrpc":"2.0","id":5,"method":"tools/call","params":{"name":"traverse","arguments":{"from":"dogbench","depth":2}}}')
    if r:
        text = r["result"]["content"][0]["text"]
        print(f"\n  traverse('dogbench', depth=2): {len(text)} chars")
        print(f"    {text}")

    # 5. summary response size
    r = mcp_call('{"jsonrpc":"2.0","id":6,"method":"tools/call","params":{"name":"summary","arguments":{}}}')
    if r:
        text = r["result"]["content"][0]["text"]
        print(f"\n  summary(): {len(text)} chars")
        print(f"    {text}")

    print()

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model", default=detect_model())
    p.add_argument("--submit", action="store_true")
    p.add_argument("--terminal", action="store_true", help="Run terminal bench only (raw MCP query cost)")
    args = p.parse_args()

    if args.terminal:
        terminal_bench()
        return

    tests = load_tests()
    if not tests:
        print("No tests found in tests/"); sys.exit(1)

    for exe in ["collar", "hermes"]:
        if subprocess.run(["which", exe], capture_output=True).returncode != 0:
            print(f"{exe} not installed"); sys.exit(1)

    total = len(AGENTS) * len(tests)
    print(f"\n  \033[1mdogbench v3\033[0m  {len(AGENTS)} agents × {len(tests)} tests = {total} total\n")

    results = {}
    for aid, (name, cmd_tpl, _) in AGENTS.items():
        color = COLORS.get(aid, "")
        agent_runs = {}
        for test in tests:
            tid = test["id"]
            test_cwd = test["cwd"]
            inp, out, passed = run_test(aid, name, cmd_tpl, test_cwd, test)
            agent_runs[tid] = {"input": inp, "output": out, "passed": passed}
            status = "\033[32m✓\033[0m" if passed else "\033[31m✗\033[0m"
            print(f"  {color}{name:<20s} {tid:<10s} {status} {fmt(inp)}t/{fmt(out)}t\033[0m")
            time.sleep(2)
        results[aid] = agent_runs

    # Summary by test category
    print(f"\n  {'Agent':<22s} {'Test':<10s} {'Pass':>4s} {'Avg In':>10s} {'Avg Out':>9s} {'Avg Total':>10s} {'Cost':>8s}")
    print("  " + "-" * 80)
    summary = {}
    for aid, (name, _, _) in [(a, n, c) for a, (n, c, w) in AGENTS.items()]:
        for test in tests:
            tid = test["id"]
            r = results[aid][tid]
            inp, out, passed = r["input"], r["output"], r["passed"]
            c = cost(inp, out, args.model) if inp > 0 else 0
            print(f"  {COLORS.get(aid,'')}{name:<22s} {tid:<10s} {'✓' if passed else '✗':>4s} {fmt(inp):>10s} {fmt(out):>9s} {fmt(inp+out):>10s} ${c:>7.4f}\033[0m")
        summary[aid] = {"name": name, "results": results[aid]}

    # JSON
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    out = {"timestamp": ts, "model": args.model, "results": {}}
    for aid, s in summary.items():
        out["results"][aid] = {"name": s["name"], "runs": s["results"]}
    print(json.dumps(out, indent=2))

    hist = SCRIPT_DIR / "results.json"
    history = []
    if hist.exists():
        try:
            history = json.loads(hist.read_text())
            if not isinstance(history, list): history = [history]
        except: pass
    history.append(out)
    if len(history) > 20: history = history[-20:]
    hist.write_text(json.dumps(history, indent=2))

    if args.submit:
        submit_results(ts)

def submit_results(ts):
    import random, string
    try:
        prs = subprocess.run(["gh", "pr", "list", "--head", "results/auto-", "--state", "open",
                              "--json", "number", "--jq", "length"],
                             cwd=str(SCRIPT_DIR), capture_output=True, text=True)
        if prs.returncode == 0 and prs.stdout.strip() and int(prs.stdout.strip()) > 0:
            print(f"\n  Skipping submit — {prs.stdout.strip()} results PR(s) already open")
            return
    except: pass

    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    branch = f"results/auto-{ts.replace(':','-').replace('T','-')[:16]}-{suffix}"
    try:
        subprocess.run(["git", "add", "results.json"], cwd=str(SCRIPT_DIR), check=True)
        subprocess.run(["git", "commit", "-m", f"chore: auto benchmark run {ts}"], cwd=str(SCRIPT_DIR), check=True)
        subprocess.run(["git", "push", "origin", f"HEAD:refs/heads/{branch}"], cwd=str(SCRIPT_DIR), check=True)
        subprocess.run(["gh", "pr", "create", "--base", "main", "--head", branch,
                        "--title", f"chore: auto benchmark run {ts}", "--body", "Auto-submitted benchmark results."],
                       cwd=str(SCRIPT_DIR), check=True)
        print(f"\n  Published to {branch} + PR created")
    except subprocess.CalledProcessError as e:
        print(f"\n  Submit failed: {e}")

if __name__ == "__main__":
    main()
