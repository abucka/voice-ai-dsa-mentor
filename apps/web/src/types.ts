export type MentorMode = "explain" | "interview" | "hints-only";
export type Screen = "landing" | "signin" | "problem";

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
