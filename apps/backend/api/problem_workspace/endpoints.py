from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from ...database import get_db
from ...db_models import SolvedProblems
from ...models import ProblemId
from ..security.security import require_authenticated_user
from .execution import evaluate_submission, execute_code
from .models import (
    LastProblemResponse,
    LastProblemUpdateRequest,
    ProblemSolution,
    RunCodeRequest,
    RunCodeResponse,
    SubmitCodeRequest,
    SubmitCodeResponse,
)
from .problem_data import SUBMISSION_TESTS, update_problem_solution

router = APIRouter()

@router.post("/api/code/run", response_model=RunCodeResponse, status_code=200)
def run_code(payload: RunCodeRequest) -> RunCodeResponse:
    tests = SUBMISSION_TESTS.get(payload.problemId, [])
    if not tests:
        raise HTTPException(status_code=422, detail="No tests found for this problem")

    return execute_code(payload.problemId, payload.language, payload.code, tests[0])

@router.post("/api/code/submit", response_model=SubmitCodeResponse, status_code=200)
def submit_code(payload: SubmitCodeRequest, db: Session = Depends(get_db)) -> SubmitCodeResponse:
    tests = SUBMISSION_TESTS.get(payload.problemId, [])
    if not tests:
        raise HTTPException(status_code=422, detail="No tests found for this problem")
    
    results, passed_tests, total_tests = evaluate_submission(payload.problemId, payload.code)

    passed = passed_tests == total_tests
    update_problem_solution(db, payload.problemId, payload.code, passed)

    return SubmitCodeResponse(
        problemId=payload.problemId,
        language=payload.language,
    passed=passed,
    passedTests=passed_tests,
    totalTests=total_tests,
        note=None if passed_tests == total_tests else "One or more sample tests failed",
        results=results,
    )

@router.get("/api/problems/{problem_id}/solution", response_model=ProblemSolution, status_code=200)
def get_solution(
    problem_id: ProblemId,
    db: Session = Depends(get_db),
) -> str:
    problem = db.get(SolvedProblems, problem_id)
    if not problem:
        return ProblemSolution(solution="", is_solved=False)
    return ProblemSolution(solution=problem.solution, is_solved=problem.is_solved)



@router.get("/api/users/me/last-problem", response_model=LastProblemResponse, status_code=200)
def get_last_problem(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> LastProblemResponse:
    user = require_authenticated_user(authorization, db)
    return LastProblemResponse(email=user.email, lastProblemId=ProblemId(user.last_problem_id))

#@router.patch("/problems/{problem_id}")
#def update_problem(problem_id: int):
#    _update_problem_solution(db, payload.problemId, payload.code)
#    return {"message": "Updated successfully"}

@router.patch("/api/users/me/last-problem", response_model=LastProblemResponse, status_code=200)
def update_last_problem(
    payload: LastProblemUpdateRequest,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> LastProblemResponse:
    user = require_authenticated_user(authorization, db)
    user.last_problem_id = payload.problemId
    db.commit()
    return LastProblemResponse(email=user.email, lastProblemId=ProblemId(user.last_problem_id))