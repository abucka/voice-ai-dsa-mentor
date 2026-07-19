export type MentorMode = "explain" | "interview" | "hints-only";
export type Screen = "landing" | "signin" | "problem";
export type CodeLanguage = "cpp" | "python";

export type DsaProblem = {
  id: string;
  title: string;
  difficulty: "Easy" | "Medium" | "Hard";
  topic: string;
  summary: string;
};

export type SignInResponse = {
  token: string;
  email: string;
  lastProblemId: DsaProblem["id"];
};

export type LastProblemResponse = {
  email: string;
  lastProblemId: DsaProblem["id"];
};

export type SubmitTestResult = {
  input: string;
  expectedOutput: string;
  actualOutput: string;
  passed: boolean;
  exitCode: number;
  timedOut: boolean;
  stderr: string;
  reason: string | null;
};

export type SubmitCodeResponse = {
  problemId: DsaProblem["id"];
  language: CodeLanguage;
  passed: boolean;
  passedTests: number;
  totalTests: number;
  note: string | null;
  results: SubmitTestResult[];
};
