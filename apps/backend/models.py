from typing import Literal, NewType

CodeLanguage = Literal["python", "cpp"]
ProblemId = NewType('ProblemId', int)
DEFAULT_PROBLEM_ID: ProblemId = 0
