import sys, os, json, importlib

def grade():
    os.chdir(sys.argv[1])  # sample/ dir
    spec = importlib.util.spec_from_file_location("solution", "solution.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    result = mod.group_anagrams(["eat","tea","tan","ate","nat","bat"])
    expected = [["eat","tea","ate"],["tan","nat"],["bat"]]
    sorted_r = sorted([sorted(g) for g in result])
    sorted_e = sorted([sorted(g) for g in expected])
    passed = sorted_r == sorted_e
    print(json.dumps({"passed": passed}))
    return 0 if passed else 1

grade()
