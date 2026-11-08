import subprocess

from apps.backend.api.problem_workspace.execution import evaluate_submission, execute_python_code
from apps.backend.models import ProblemId

PROBLEM_ZERO = ProblemId(0)  # "Longest Substring Without Repeating Characters"
PROBLEM_TWO_SUM = ProblemId(1)  # "Two Sum" -- takes two positional arguments

CORRECT_SOLUTION = """
def solve(s):
    seen = {}
    start = 0
    best = 0
    for i, ch in enumerate(s):
        if ch in seen and seen[ch] >= start:
            start = seen[ch] + 1
        seen[ch] = i
        best = max(best, i - start + 1)
    return best
"""

CORRECT_TWO_SUM_SOLUTION = """
def solve(nums, target):
    seen = {}
    for i, n in enumerate(nums):
        complement = target - n
        if complement in seen:
            return [seen[complement], i]
        seen[n] = i
    return []
"""


def test_execute_python_code_runs_and_returns_stdout():
    result = execute_python_code(PROBLEM_ZERO, CORRECT_SOLUTION, test_row=["abcabcbb", "3"])

    assert result.exitCode == 0
    assert result.timedOut is False
    assert result.stdout.strip() == "3"
    assert result.stderr == ""


def test_execute_python_code_uses_each_test_rows_own_arguments():
    # Same solution, different sample rows -- each must be called with its own input
    # rather than the harness re-running a single fixed call for every row.
    first = execute_python_code(PROBLEM_ZERO, CORRECT_SOLUTION, test_row=["abcabcbb", "3"])
    second = execute_python_code(PROBLEM_ZERO, CORRECT_SOLUTION, test_row=["bbbbb", "1"])

    assert first.stdout.strip() == "3"
    assert second.stdout.strip() == "1"


def test_execute_python_code_reports_a_missing_solve_function():
    result = execute_python_code(PROBLEM_ZERO, code="", test_row=["abcabcbb", "3"])

    assert result.exitCode != 0
    assert result.timedOut is False
    assert "solve" in result.stderr


def test_execute_python_code_reports_runtime_errors_from_user_code():
    broken_solution = "def solve(s):\n    return 1 / 0\n"

    result = execute_python_code(PROBLEM_ZERO, broken_solution, test_row=["abcabcbb", "3"])

    assert result.exitCode != 0
    assert "ZeroDivisionError" in result.stderr


def test_execute_python_code_times_out_on_an_infinite_loop():
    infinite_loop_solution = "def solve(s):\n    while True:\n        pass\n"

    result = execute_python_code(PROBLEM_ZERO, infinite_loop_solution, test_row=["abcabcbb", "3"])

    assert result.timedOut is True
    assert result.exitCode == 124


def test_execute_python_code_marks_signal_kill_as_a_timeout(monkeypatch):
    completed = subprocess.CompletedProcess(args=["python"], returncode=-9, stdout="", stderr="killed")

    monkeypatch.setattr("apps.backend.api.problem_workspace.execution.subprocess.run", lambda *args, **kwargs: completed)

    result = execute_python_code(PROBLEM_ZERO, "def solve(s):\n    while True:\n        pass\n", test_row=["abcabcbb", "3"])

    assert result.timedOut is True
    assert result.exitCode == 124
    assert "killed" in result.stderr.lower()


def test_evaluate_submission_grades_a_correct_solution_against_all_sample_tests():
    results, passed_tests, total_tests = evaluate_submission(PROBLEM_ZERO, CORRECT_SOLUTION)

    assert total_tests == 3
    assert passed_tests == 3
    assert [r.passed for r in results] == [True, True, True]
    assert [r.actualOutput.strip() for r in results] == ["3", "1", "3"]


def test_evaluate_submission_supports_multi_argument_problems():
    # Regression test: Two Sum's rows are `[nums, target, expected]` (3 elements).
    # This used to crash grading because the old harness always re-ran a single
    # hardcoded call regardless of which row was being checked.
    results, passed_tests, total_tests = evaluate_submission(PROBLEM_TWO_SUM, CORRECT_TWO_SUM_SOLUTION)

    assert total_tests == 3
    assert passed_tests == 3


PROBLEM_MERGE_TWO_SORTED_LISTS = ProblemId(4)
PROBLEM_INVERT_BINARY_TREE = ProblemId(7)
PROBLEM_SYMMETRIC_TREE = ProblemId(13)

CORRECT_MERGE_TWO_SORTED_LISTS_SOLUTION = """
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

def solve(l1, l2):
    dummy = ListNode()
    tail = dummy
    while l1 and l2:
        if l1.val <= l2.val:
            tail.next = l1
            l1 = l1.next
        else:
            tail.next = l2
            l2 = l2.next
        tail = tail.next
    tail.next = l1 or l2
    return dummy.next
"""

CORRECT_INVERT_BINARY_TREE_SOLUTION = """
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def solve(root):
    if root is None:
        return None
    root.left, root.right = solve(root.right), solve(root.left)
    return root
"""

CORRECT_SYMMETRIC_TREE_SOLUTION = """
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def solve(root):
    def is_mirror(a, b):
        if a is None and b is None:
            return True
        if a is None or b is None:
            return False
        return a.val == b.val and is_mirror(a.left, b.right) and is_mirror(a.right, b.left)
    return is_mirror(root, root)
"""


def test_evaluate_submission_supports_linked_list_problems():
    # Regression test: Merge Two Sorted Lists' harness used to reference undefined
    # `l1_head`/`l2_head` variables and crash with NameError for every submission.
    results, passed_tests, total_tests = evaluate_submission(
        PROBLEM_MERGE_TWO_SORTED_LISTS, CORRECT_MERGE_TWO_SORTED_LISTS_SOLUTION
    )

    assert total_tests == 3
    assert passed_tests == 3


def test_evaluate_submission_supports_binary_tree_problems_that_return_a_tree():
    # Regression test: Invert Binary Tree's harness used to reference an undefined
    # `root` variable and crash with NameError for every submission.
    results, passed_tests, total_tests = evaluate_submission(
        PROBLEM_INVERT_BINARY_TREE, CORRECT_INVERT_BINARY_TREE_SOLUTION
    )

    assert total_tests == 3
    assert passed_tests == 3


def test_evaluate_submission_supports_binary_tree_problems_that_return_a_boolean():
    results, passed_tests, total_tests = evaluate_submission(
        PROBLEM_SYMMETRIC_TREE, CORRECT_SYMMETRIC_TREE_SOLUTION
    )

    assert total_tests == 3
    assert passed_tests == 3
