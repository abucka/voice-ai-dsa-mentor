import { DsaProblem } from "../types";
import { PROBLEMS } from "./problems";

export const CODE_LANGUAGES = [
  { id: "python", label: "Python", filename: "main.py" }
];

export function getSolveTemplate(problemId: DsaProblem["id"]): string {
  return PROBLEMS[problemId].template.join("\n")
}