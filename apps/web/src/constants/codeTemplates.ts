import { CodeLanguage, DsaProblem } from "../types";
import { PROBLEMS } from "./problems";

export const CODE_LANGUAGES = [
  { id: "python", label: "Python", filename: "main.py" },
  { id: "cpp", label: "C++", filename: "main.cpp" }
] as const;

export function getSolveTemplate(problemId: DsaProblem["id"], language: CodeLanguage): string {
  if (language === "cpp") {
    return [
      "#include <bits/stdc++.h>",
      "using namespace std;",
      "",
      "// Replace the placeholder below with your C++ solution.",
      "// The backend calls your solve() function directly during runs and submissions.",
      "int solve() {",
      "    return 0;",
      "}",
      ""
    ].join("\n");
  }

  return PROBLEMS[problemId].template.join("\n");
}