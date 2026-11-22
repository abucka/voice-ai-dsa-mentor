import { CodeLanguage, DsaProblem } from "../types";
import { LANG_STORAGE_KEY, PROBLEMS, STORAGE_KEY } from "../constants/problems";

export function getInitialProblemId(): number {
  if (typeof window === "undefined") {
    return PROBLEMS[0].id;
  }

  const saved = Number(window.localStorage.getItem(STORAGE_KEY));
  return PROBLEMS.some((problem) => problem.id === saved) ? (saved as number) : PROBLEMS[0].id;
}

export function getInitialLangId(problemId: DsaProblem["id"]): CodeLanguage {
  if (typeof window === "undefined") {
    return "python";
  }

  const saved = window.localStorage.getItem(`${LANG_STORAGE_KEY}:${problemId}`);
  return saved === "python" || saved === "cpp" ? saved : "python";
}

export function saveProblemIdLocally(problemId: DsaProblem["id"]) {
  window.localStorage.setItem(STORAGE_KEY, String(problemId));
}

export function saveLangIdLocally(problemId: DsaProblem["id"], language: CodeLanguage) {
  window.localStorage.setItem(`${LANG_STORAGE_KEY}:${problemId}`, language);
}
