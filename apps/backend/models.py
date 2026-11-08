from typing import Literal, NewType

CodeLanguage = Literal["python"]
ProblemId = NewType('ProblemId', int)
DEFAULT_PROBLEM_ID: ProblemId = 0
