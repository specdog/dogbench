import sys, os, json, re

def grade():
    cwd = sys.argv[1]
    # Read the agent's answer from answer.txt
    answer_path = os.path.join(cwd, "answer.txt")
    if not os.path.exists(answer_path):
        print(json.dumps({"passed": False, "reason": "no answer.txt"}))
        return 1

    answer = open(answer_path).read().lower()

    # Ground truth: entities defined in the dogbench .dag
    required = [
        ("dogbench", "entity"),
        ("agents", "entity"),
        ("benchmark", "entity"),
        ("telemetry", "entity"),
        ("deps", "entity"),
    ]

    found = 0
    missing = []
    for name, etype in required:
        # Check if answer mentions both name and type
        if name in answer and (etype in answer or "entity" in answer):
            found += 1
        else:
            missing.append(name)

    passed = found == len(required)
    print(json.dumps({
        "passed": passed,
        "found": found,
        "required": len(required),
        "missing": missing,
        "answer_preview": answer[:200]
    }))
    return 0 if passed else 1

grade()
