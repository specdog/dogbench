import sys, os, json

def grade():
    cwd = sys.argv[1]
    answer_path = os.path.join(cwd, "answer.txt")
    if not os.path.exists(answer_path):
        print(json.dumps({"passed": False, "reason": "no answer.txt"}))
        return 1

    answer = open(answer_path).read().lower()

    # Ground truth: key entity/component names from the project
    required = ["dogbench", "benchmark", "agents", "telemetry", "deps"]

    found = 0
    missing = []
    for name in required:
        if name in answer:
            found += 1
        else:
            missing.append(name)

    # Pass if found at least 4 out of 5
    passed = found >= 4
    print(json.dumps({
        "passed": passed,
        "found": found,
        "required": len(required),
        "missing": missing,
        "answer_preview": answer[:200]
    }))
    return 0 if passed else 1

grade()
