import { DsaProblem } from "../types";
import { PROBLEMS, STORAGE_KEY } from "../constants/problems";

export function getInitialProblemId(): number {
  if (typeof window === "undefined") {
    return PROBLEMS[0].id;
  }

  const saved = Number(window.localStorage.getItem(STORAGE_KEY));
  return PROBLEMS.some((problem) => problem.id === saved) ? (saved as number) : PROBLEMS[0].id;
}

export function saveProblemIdLocally(problemId: DsaProblem["id"]) {
  window.localStorage.setItem(STORAGE_KEY, String(problemId));
}
