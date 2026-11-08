CORRECT_LONGEST_SUBSTRING_SOLUTION = """
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


def test_run_code_returns_stdout_for_a_valid_submission(client):
    response = client.post(
        "/api/code/run",
        json={"problemId": 0, "language": "python", "code": CORRECT_LONGEST_SUBSTRING_SOLUTION},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["exitCode"] == 0
    assert body["stdout"].strip() == "3"
    assert body["timedOut"] is False


def test_run_code_returns_422_for_an_unknown_problem_id(client):
    response = client.post(
        "/api/code/run",
        json={"problemId": 9999, "language": "python", "code": CORRECT_LONGEST_SUBSTRING_SOLUTION},
    )

    assert response.status_code == 422


def test_run_code_rejects_an_empty_code_body(client):
    response = client.post(
        "/api/code/run",
        json={"problemId": 0, "language": "python", "code": ""},
    )

    assert response.status_code == 422


def test_submit_code_reports_per_test_results(client):
    response = client.post(
        "/api/code/submit",
        json={"problemId": 0, "language": "python", "code": CORRECT_LONGEST_SUBSTRING_SOLUTION},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["totalTests"] == 3
    assert len(body["results"]) == 3
    assert body["passed"] is True
    assert body["passedTests"] == 3


def test_run_code_works_for_a_multi_argument_problem(client):
    # Regression test: Two Sum's rows are `[nums, target, expected]`. The "Run"
    # endpoint used to crash on this shape (`stdin_text, _ = tests[0]`).
    response = client.post(
        "/api/code/run",
        json={"problemId": 1, "language": "python", "code": CORRECT_TWO_SUM_SOLUTION},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["exitCode"] == 0
    assert body["stdout"].strip() == "[0,1]"


def test_submit_code_works_for_a_multi_argument_problem(client):
    response = client.post(
        "/api/code/submit",
        json={"problemId": 1, "language": "python", "code": CORRECT_TWO_SUM_SOLUTION},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["totalTests"] == 3
    assert body["passed"] is True
    assert body["passedTests"] == 3


def test_submit_code_reports_a_runtime_error_reason(client):
    broken_solution = "def solve(s):\n    return 1 / 0\n"

    response = client.post(
        "/api/code/submit",
        json={"problemId": 0, "language": "python", "code": broken_solution},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["passed"] is False
    assert all(result["reason"] == "Runtime error" for result in body["results"])


def test_call_openai_tutor_uses_openai_client(monkeypatch):
    from types import SimpleNamespace

    import apps.backend.api.ai_services.ai_services as ai_services

    class FakeResponse:
        class Choice:
            def __init__(self):
                self.message = SimpleNamespace(content="Helpful hint")

        choices = [Choice()]

    class FakeOpenAI:
        def __init__(self, api_key):
            self.api_key = api_key
            self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

        def _create(self, **kwargs):
            assert kwargs["model"] == "gpt-4.1-mini"
            assert kwargs["messages"][1]["role"] == "user"
            return FakeResponse()

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(ai_services, "OpenAI", FakeOpenAI, raising=False)

    answer = ai_services.call_openai_tutor(0, "Why is my code wrong?", "print(1)", "explain")

    assert answer == "Helpful hint"
