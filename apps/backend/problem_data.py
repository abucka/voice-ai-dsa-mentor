from .models import ProblemId
import json

# Open the file and parse the JSON data into a dictionary
with open('data/data.json', 'r', encoding='utf-8') as file:
    PROBLEM_DATA = json.load(file)

SUBMISSION_TESTS: dict[int, list[tuple[str, str]]] = {
    id: element["tests"] for id, element in enumerate(PROBLEM_DATA["exercises"])
}

PROBLEM_SUMMARIES: dict[ProblemId, str] = {
    id: element["title"] for id, element in enumerate(PROBLEM_DATA["exercises"])
}

def normalize_output(value: str) -> str:
    return value.strip()

def get_problem_summary(problem_id: ProblemId) -> str:
    return PROBLEM_SUMMARIES[problem_id]

def build_python_harness(problem_id: ProblemId) -> str:
    return f"""
import sys

if "solve" not in globals():
    raise NameError("Missing required function: solve")

{PROBLEM_DATA["exercises"][problem_id]["execution"]}

if isinstance(result, (list, tuple)):
    print(" ".join(str(x) for x in result))
else:
    print(result)
"""