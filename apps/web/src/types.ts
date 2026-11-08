export type Screen = "landing" | "signin" | "problem";
export type CodeLanguage = "python";

export type DsaProblem = {
  id: number;
  title: string;
  difficulty: string;
  topic: string;
  summary: string;
  template: string[]
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

export type HelpTutorResponse = {
  problemId: DsaProblem["id"];
  answer: string;
};
