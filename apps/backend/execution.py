import subprocess
import sys
import tempfile
from pathlib import Path

from .models import CodeLanguage, ProblemId, RunCodeResponse, SubmitTestResult
from .problem_data import SUBMISSION_TESTS, build_python_harness, normalize_output


def execute_python_code(problem_id: ProblemId, code: str, stdin_text: str) -> RunCodeResponse:
    timeout_seconds = 5

    with tempfile.TemporaryDirectory() as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        code_file = temp_dir / "main.py"
        wrapped_code = f"{code}\n\n{build_python_harness(problem_id)}"
        code_file.write_text(wrapped_code, encoding="utf-8")

        try:
            completed = subprocess.run(
                [sys.executable, str(code_file)],
                cwd=temp_dir,
                input=stdin_text,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
            )
        except subprocess.TimeoutExpired as error:
            return RunCodeResponse(
                language="python",
                stdout=error.stdout or "",
                stderr=error.stderr or "Timed out while running Python code",
                exitCode=124,
                timedOut=True,
            )

        return RunCodeResponse(
            language="python",
            stdout=completed.stdout,
            stderr=completed.stderr,
            exitCode=completed.returncode,
            timedOut=False,
        )


def execute_code(problem_id: ProblemId, language: CodeLanguage, code: str, stdin_text: str) -> RunCodeResponse:
    return execute_python_code(problem_id, code, stdin_text)


def evaluate_submission(problem_id: ProblemId, code: str) -> tuple[list[SubmitTestResult], int, int]:
    tests = SUBMISSION_TESTS.get(problem_id, [])
    results: list[SubmitTestResult] = []
    passed_tests = 0

    for test_input, expected_output in tests:
        execution_result = execute_python_code(problem_id, code, test_input)
        actual_output = execution_result.stdout
        passed = (
            not execution_result.timedOut
            and execution_result.exitCode == 0
            and normalize_output(actual_output) == normalize_output(expected_output)
        )
        if passed:
            passed_tests += 1

        results.append(
            SubmitTestResult(
                input=test_input,
                expectedOutput=expected_output,
                actualOutput=actual_output,
                passed=passed,
                exitCode=execution_result.exitCode,
                timedOut=execution_result.timedOut,
                stderr=execution_result.stderr,
                reason=None if passed else "Output mismatch" if not execution_result.stderr else "Runtime error",
            )
        )

    return results, passed_tests, len(tests)
