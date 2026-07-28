from .models import ProblemId
import json

# Open the file and parse the JSON data into a dictionary
with open('data/data.json', 'r', encoding='utf-8') as file:
    PROBLEM_DATA = json.load(file)

# Each test row is `[*args, expected_output]`: every element except the last is a
# positional argument to call the learner's `solve` function with, and the last
# element is the expected (string) output for that specific call.
SUBMISSION_TESTS: dict[int, list[list]] = {
    id: element["tests"] for id, element in enumerate(PROBLEM_DATA["exercises"])
}

PROBLEM_SUMMARIES: dict[ProblemId, str] = {
    id: element["title"] for id, element in enumerate(PROBLEM_DATA["exercises"])
}

def normalize_output(value: str) -> str:
    return value.strip()

def get_problem_summary(problem_id: ProblemId) -> str:
    return PROBLEM_SUMMARIES[problem_id]

def test_arguments(test_row: list) -> list:
    """The positional arguments to call `solve` with for a given sample test row."""
    return test_row[:-1]

def expected_output(test_row: list) -> str:
    """The expected stdout for a given sample test row."""
    return test_row[-1]

def build_python_harness(problem_id: ProblemId, test_row: list) -> str:
    """Build the harness that calls `solve` with this specific test row's arguments.

    Values come from static, developer-authored `data/data.json` (not learner input),
    so `repr()` is safe here purely to serialize JSON-decoded literals (str/int/list/
    bool/None) back into equivalent Python source.
    """
    call_args = ", ".join(repr(arg) for arg in test_arguments(test_row))
    return f"""
import sys

if "solve" not in globals():
    raise NameError("Missing required function: solve")

result = solve({call_args})

if isinstance(result, (list, tuple)):
    print("[" + ",".join(str(x) for x in result) + "]")
else:
    print(result)
"""