from .models import ProblemId

SUBMISSION_TESTS: dict[ProblemId, list[tuple[str, str]]] = {
    "two-sum": [
        ("4 9\n2 7 11 15\n", "0 1\n"),
        ("3 6\n3 2 4\n", "1 2\n"),
    ],
    "valid-parentheses": [
        ("([{}])\n", "true\n"),
        ("([)]\n", "false\n"),
    ],
    "longest-substring-no-repeat": [
        ("abcabcbb\n", "3\n"),
        ("bbbbb\n", "1\n"),
    ],
    "merge-k-sorted-lists": [
        ("3\n1 4 5\n1 3 4\n2 6\n", "1 1 2 3 4 4 5 6\n"),
        ("2\n1 2\n3 4\n", "1 2 3 4\n"),
    ],
}

PROBLEM_SUMMARIES: dict[ProblemId, str] = {
    "two-sum": "Find two indices whose values add up to a target in linear time.",
    "valid-parentheses": "Validate bracket order using stack pushes and pops.",
    "longest-substring-no-repeat": "Use a sliding window to find the longest substring with unique characters.",
    "merge-k-sorted-lists": "Merge multiple sorted linked lists efficiently.",
}


def normalize_output(value: str) -> str:
    return value.strip()


def get_problem_summary(problem_id: ProblemId) -> str:
    return PROBLEM_SUMMARIES[problem_id]


def build_python_harness(problem_id: ProblemId) -> str:
    if problem_id == "two-sum":
        return """
import sys

if "solve" not in globals():
    raise NameError("Missing required function: solve")

parts = sys.stdin.readline().strip().split()
n = int(parts[0])
target = int(parts[1])
nums = list(map(int, sys.stdin.readline().strip().split()))[:n]
result = solve(nums, target)

if isinstance(result, (list, tuple)):
    print(" ".join(str(x) for x in result))
else:
    print(result)
"""

    if problem_id == "valid-parentheses":
        return """
import sys

if "solve" not in globals():
    raise NameError("Missing required function: solve")

s = sys.stdin.readline().rstrip("\n")
result = solve(s)
print("true" if bool(result) else "false")
"""

    if problem_id == "longest-substring-no-repeat":
        return """
import sys

if "solve" not in globals():
    raise NameError("Missing required function: solve")

s = sys.stdin.readline().rstrip("\n")
result = solve(s)
print(result)
"""

    return """
import sys

if "solve" not in globals():
    raise NameError("Missing required function: solve")

k = int(sys.stdin.readline().strip())
lists = []
for _ in range(k):
    line = sys.stdin.readline().strip()
    lists.append(list(map(int, line.split())) if line else [])

result = solve(lists)
if isinstance(result, (list, tuple)):
    print(" ".join(str(x) for x in result))
else:
    print(result)
"""
