import sys, os, json

def grade():
    cwd = sys.argv[1]
    answer_path = os.path.join(cwd, "answer.txt")
    if not os.path.exists(answer_path):
        print(json.dumps({"passed": False, "reason": "no answer.txt"}))
        return 1

    answer = open(answer_path).read().lower()

    # Check for correct answer: 3 hours, 180 miles
    has_time = "3" in answer and ("hour" in answer or "hr" in answer)
    has_distance = "180" in answer and ("mile" in answer or "mi" in answer)
    has_from_a = ("from station a" in answer or "from a" in answer or "miles from station a" in answer)

    passed = has_time and has_distance
    print(json.dumps({
        "passed": passed,
        "has_time": has_time,
        "has_distance": has_distance,
        "has_from_a": has_from_a,
        "answer_preview": answer[:200]
    }))
    return 0 if passed else 1

grade()
