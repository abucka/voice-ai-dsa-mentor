import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from ...models import CodeLanguage, ProblemId
from .models import RunCodeResponse, SubmitTestResult
from .problem_data import SUBMISSION_TESTS, build_python_harness, expected_output, normalize_output, test_arguments

# Untrusted user code runs as a plain subprocess, not inside a container/VM. This is NOT a
# strong sandbox: it will not stop syscalls, filesystem access outside cwd, or slow network
# calls made from within the submitted code. For a production deployment, run submissions in
# an isolated container/microVM (e.g. gVisor, Firecracker, Docker with seccomp + no network)
# instead of relying on subprocess limits alone.
MAX_OUTPUT_BYTES = 64 * 1024
_MINIMAL_ENV = {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "PYTHONIOENCODING": "utf-8"}


def _limit_subprocess_resources() -> None:
    """Best-effort resource caps applied in the child process before exec (POSIX only)."""
    try:
        import resource

        one_mb = 1024 * 1024
        resource.setrlimit(resource.RLIMIT_CPU, (5, 5))
        resource.setrlimit(resource.RLIMIT_AS, (256 * one_mb, 256 * one_mb))
        resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))
        resource.setrlimit(resource.RLIMIT_NPROC, (32, 32))
    except (ImportError, ValueError, OSError):
        # resource module is POSIX-only and some limits aren't settable on every platform.
        pass


def _cpp_literal(value) -> str:
    if value is None:
        return "nullptr"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)
    if isinstance(value, str):
        if value.startswith("[") and value.endswith("]"):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    return "std::vector<int>{" + ", ".join(_cpp_literal(item) for item in parsed) + "}" if parsed else "std::vector<int>{}"
            except (TypeError, ValueError):
                pass
        return json.dumps(value)
    if isinstance(value, list):
        if not value:
            return "std::vector<int>{}"
        return "std::vector<int>{" + ", ".join(_cpp_literal(item) for item in value) + "}"
    return json.dumps(str(value))


def _build_cpp_harness(test_row: list) -> str:
    args = test_arguments(test_row)
    expected = expected_output(test_row)
    declarations = []
    names: list[str] = []

    for index, value in enumerate(args):
        arg_name = f"arg{index}"
        names.append(arg_name)
        declarations.append(f"    auto {arg_name} = {_cpp_literal(value)};")

    call = ", ".join(names)
    if expected.startswith("["):
        return f"""
int main() {{
{chr(10).join(declarations)}
    auto result = solve({call});
    std::cout << "[";
    for (size_t index = 0; index < result.size(); ++index) {{
        if (index > 0) std::cout << ",";
        std::cout << result[index];
    }}
    std::cout << "]";
    return 0;
}}
"""

    if expected in {"True", "False"}:
        return f"""
int main() {{
{chr(10).join(declarations)}
    auto result = solve({call});
    std::cout << (result ? "True" : "False");
    return 0;
}}
"""

    return f"""
int main() {{
{chr(10).join(declarations)}
    auto result = solve({call});
    std::cout << result;
    return 0;
}}
"""


def execute_python_code(problem_id: ProblemId, code: str, test_row: list) -> RunCodeResponse:
    timeout_seconds = 5
    input_text = ", ".join(repr(arg) for arg in test_arguments(test_row))
    expected_output_value = expected_output(test_row)

    with tempfile.TemporaryDirectory() as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        code_file = temp_dir / "main.py"
        wrapped_code = f"{code}\n\n{build_python_harness(problem_id, test_row)}"
        code_file.write_text(wrapped_code, encoding="utf-8")

        try:
            completed = subprocess.run(
                [sys.executable, "-I", str(code_file)],
                cwd=temp_dir,
                input="",
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                env=_MINIMAL_ENV,
                preexec_fn=_limit_subprocess_resources if sys.platform != "win32" else None,
            )
        except subprocess.TimeoutExpired as error:
            return RunCodeResponse(
                language="python",
                input=input_text,
                expectedOutput=expected_output_value,
                stdout=(error.stdout or "")[:MAX_OUTPUT_BYTES],
                stderr=(error.stderr or "Timed out while running Python code")[:MAX_OUTPUT_BYTES],
                exitCode=124,
                timedOut=True,
            )

        timed_out = completed.returncode < 0
        if timed_out:
            return RunCodeResponse(
                language="python",
                input=input_text,
                expectedOutput=expected_output_value,
                stdout=completed.stdout[:MAX_OUTPUT_BYTES],
                stderr=(completed.stderr or "Timed out while running Python code")[:MAX_OUTPUT_BYTES],
                exitCode=124,
                timedOut=True,
            )

        return RunCodeResponse(
            language="python",
            input=input_text,
            expectedOutput=expected_output_value,
            stdout=completed.stdout[:MAX_OUTPUT_BYTES],
            stderr=completed.stderr[:MAX_OUTPUT_BYTES],
            exitCode=completed.returncode,
            timedOut=False,
        )


def execute_cpp_code(problem_id: ProblemId, code: str, test_row: list) -> RunCodeResponse:
    timeout_seconds = 5
    input_text = ", ".join(repr(arg) for arg in test_arguments(test_row))
    expected_output_value = expected_output(test_row)
    compiler = shutil.which("g++") or shutil.which("c++")

    if not compiler:
        return RunCodeResponse(
            language="cpp",
            input=input_text,
            expectedOutput=expected_output_value,
            stdout="",
            stderr="C++ compiler not found. Install g++ or clang++ and try again.",
            exitCode=127,
            timedOut=False,
        )

    with tempfile.TemporaryDirectory() as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        bits_dir = temp_dir / "bits"
        bits_dir.mkdir(parents=True, exist_ok=True)
        compatibility_header = bits_dir / "stdc++.h"
        compatibility_header.write_text(
            "#pragma once\n"
            "#include <algorithm>\n"
            "#include <array>\n"
            "#include <cmath>\n"
            "#include <cstdlib>\n"
            "#include <iostream>\n"
            "#include <map>\n"
            "#include <numeric>\n"
            "#include <queue>\n"
            "#include <set>\n"
            "#include <sstream>\n"
            "#include <stack>\n"
            "#include <string>\n"
            "#include <tuple>\n"
            "#include <unordered_map>\n"
            "#include <unordered_set>\n"
            "#include <utility>\n"
            "#include <vector>\n",
            encoding="utf-8",
        )

        code_file = temp_dir / "main.cpp"
        wrapped_code = f"{code}\n\n{_build_cpp_harness(test_row)}"
        code_file.write_text(wrapped_code, encoding="utf-8")
        executable = temp_dir / "solution"

        compile_result = subprocess.run(
            [compiler, "-std=c++17", "-I", str(temp_dir), str(code_file), "-O2", "-o", str(executable)],
            cwd=temp_dir,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            env=_MINIMAL_ENV,
        )
        if compile_result.returncode != 0:
            return RunCodeResponse(
                language="cpp",
                input=input_text,
                expectedOutput=expected_output_value,
                stdout="",
                stderr=compile_result.stderr or compile_result.stdout or "C++ compilation failed.",
                exitCode=compile_result.returncode,
                timedOut=False,
            )

        try:
            completed = subprocess.run(
                [str(executable)],
                cwd=temp_dir,
                input="",
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                env=_MINIMAL_ENV,
            )
        except subprocess.TimeoutExpired as error:
            return RunCodeResponse(
                language="cpp",
                input=input_text,
                expectedOutput=expected_output_value,
                stdout=(error.stdout or "")[:MAX_OUTPUT_BYTES],
                stderr=(error.stderr or "Timed out while running C++ code")[:MAX_OUTPUT_BYTES],
                exitCode=124,
                timedOut=True,
            )

        timed_out = completed.returncode < 0
        if timed_out:
            return RunCodeResponse(
                language="cpp",
                input=input_text,
                expectedOutput=expected_output_value,
                stdout=completed.stdout[:MAX_OUTPUT_BYTES],
                stderr=(completed.stderr or "Timed out while running C++ code")[:MAX_OUTPUT_BYTES],
                exitCode=124,
                timedOut=True,
            )

        return RunCodeResponse(
            language="cpp",
            input=input_text,
            expectedOutput=expected_output_value,
            stdout=completed.stdout[:MAX_OUTPUT_BYTES],
            stderr=completed.stderr[:MAX_OUTPUT_BYTES],
            exitCode=completed.returncode,
            timedOut=False,
        )


def execute_code(problem_id: ProblemId, language: CodeLanguage, code: str, test_row: list) -> RunCodeResponse:
    if language == "cpp":
        return execute_cpp_code(problem_id, code, test_row)
    return execute_python_code(problem_id, code, test_row)


def evaluate_submission(problem_id: ProblemId, code: str, language: CodeLanguage = "python") -> tuple[list[SubmitTestResult], int, int]:
    tests = SUBMISSION_TESTS.get(problem_id, [])
    results: list[SubmitTestResult] = []
    passed_tests = 0

    for test_row in tests:
        expected = expected_output(test_row)
        execution_result = execute_code(problem_id, language, code, test_row)
        actual_output = execution_result.stdout
        passed = (
            not execution_result.timedOut
            and execution_result.exitCode == 0
            and normalize_output(actual_output) == normalize_output(expected)
        )
        if passed:
            passed_tests += 1

        results.append(
            SubmitTestResult(
                input=", ".join(repr(arg) for arg in test_arguments(test_row)),
                expectedOutput=expected,
                actualOutput=actual_output,
                passed=passed,
                exitCode=execution_result.exitCode,
                timedOut=execution_result.timedOut,
                stderr=execution_result.stderr,
                reason=None if passed else "Output mismatch" if not execution_result.stderr else "Runtime error",
            )
        )

    return results, passed_tests, len(tests)
