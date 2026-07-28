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

def _template_source(problem_id: ProblemId) -> str:
    return "\n".join(PROBLEM_DATA["exercises"][problem_id]["template"])

def _uses_linked_list(problem_id: ProblemId) -> bool:
    return "class ListNode" in _template_source(problem_id)

def _uses_binary_tree(problem_id: ProblemId) -> bool:
    return "class TreeNode" in _template_source(problem_id)

def _linked_list_harness(args: list) -> str:
    """Harness for problems whose `solve` takes/returns linked lists.

    Sample test args are JSON-encoded array strings (e.g. `"[1,2,4]"`); each is
    parsed and built into a chain of the learner's own `ListNode` class before
    calling `solve`, and the returned list head is serialized back to the same
    bracketed array format used by `data/data.json`'s expected outputs.
    """
    call_args = ", ".join(f"_list_to_linked_list({arg!r})" for arg in args)
    return f"""
import json

if "solve" not in globals():
    raise NameError("Missing required function: solve")
if "ListNode" not in globals():
    raise NameError("Missing required class: ListNode")

def _list_to_linked_list(raw_json):
    values = json.loads(raw_json)
    head = None
    tail = None
    for value in values:
        node = ListNode(value)
        if head is None:
            head = node
        else:
            tail.next = node
        tail = node
    return head

def _linked_list_to_list(head):
    values = []
    node = head
    while node is not None:
        values.append(node.val)
        node = node.next
    return values

result = solve({call_args})
print("[" + ",".join(str(x) for x in _linked_list_to_list(result)) + "]")
"""

def _binary_tree_harness(args: list, returns_tree: bool) -> str:
    """Harness for problems whose `solve` takes/returns binary trees.

    Sample test args are JSON-encoded, LeetCode-style level-order array strings
    (e.g. `"[1,2,2,null,3,null,3]"`); each is parsed and built into the learner's
    own `TreeNode` class before calling `solve`. If `solve` returns a tree, it is
    serialized back to the same level-order array format; otherwise (e.g. a
    boolean check like "is this tree symmetric?") the raw result is printed.
    """
    call_args = ", ".join(f"_list_to_tree({arg!r})" for arg in args)
    output_expr = "_tree_to_list_str(result)" if returns_tree else "result"
    return f"""
import json

if "solve" not in globals():
    raise NameError("Missing required function: solve")
if "TreeNode" not in globals():
    raise NameError("Missing required class: TreeNode")

def _list_to_tree(raw_json):
    values = json.loads(raw_json)
    if not values or values[0] is None:
        return None
    root = TreeNode(values[0])
    queue = [root]
    i = 1
    while queue and i < len(values):
        node = queue.pop(0)
        if i < len(values):
            left_value = values[i]
            i += 1
            if left_value is not None:
                node.left = TreeNode(left_value)
                queue.append(node.left)
        if i < len(values):
            right_value = values[i]
            i += 1
            if right_value is not None:
                node.right = TreeNode(right_value)
                queue.append(node.right)
    return root

def _tree_to_list_str(root):
    if root is None:
        return "[]"
    values = []
    queue = [root]
    while queue:
        node = queue.pop(0)
        if node is None:
            values.append(None)
            continue
        values.append(node.val)
        queue.append(node.left)
        queue.append(node.right)
    while values and values[-1] is None:
        values.pop()
    return "[" + ",".join(str(v) for v in values) + "]"

result = solve({call_args})
print({output_expr})
"""

def build_python_harness(problem_id: ProblemId, test_row: list) -> str:
    """Build the harness that calls `solve` with this specific test row's arguments.

    Values come from static, developer-authored `data/data.json` (not learner input),
    so `repr()` is safe here purely to serialize JSON-decoded literals (str/int/list/
    bool/None) back into equivalent Python source.
    """
    args = test_arguments(test_row)

    if _uses_linked_list(problem_id):
        return _linked_list_harness(args)

    if _uses_binary_tree(problem_id):
        returns_tree = expected_output(test_row).strip() not in ("True", "False")
        return _binary_tree_harness(args, returns_tree)

    call_args = ", ".join(repr(arg) for arg in args)
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