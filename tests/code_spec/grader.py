import sys, os, json, importlib.util

def grade():
    cwd = sys.argv[1]
    solution_path = os.path.join(cwd, "solution.py")

    if not os.path.exists(solution_path):
        print(json.dumps({"passed": False, "reason": "no solution.py"}))
        return 1

    # Import solution.py
    spec = importlib.util.spec_from_file_location("solution", solution_path)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception as e:
        print(json.dumps({"passed": False, "reason": f"import error: {e}"}))
        return 1

    # Check function exists
    if not hasattr(mod, 'validate_benchmark'):
        print(json.dumps({"passed": False, "reason": "no validate_benchmark function"}))
        return 1

    fn = mod.validate_benchmark

    # Test cases
    tests = [
        ({"task": "test", "model": "deepseek", "agents": ["hermes"]}, True),
        ({"task": "test", "model": "deepseek"}, False),  # missing agents
        ({}, False),
        ({"task": "x", "model": "y", "agents": []}, True),
    ]

    passed = 0
    for data, expected in tests:
        try:
            result = fn(data)
            if result == expected:
                passed += 1
        except:
            pass

    ok = passed == len(tests)
    print(json.dumps({"passed": ok, "score": f"{passed}/{len(tests)}"}))
    return 0 if ok else 1

grade()
