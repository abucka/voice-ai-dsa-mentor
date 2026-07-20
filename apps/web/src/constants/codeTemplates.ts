import { CodeLanguage, DsaProblem } from "../types";

export const CODE_LANGUAGES: Array<{ id: CodeLanguage; label: string; filename: string }> = [
  { id: "cpp", label: "C++", filename: "main.cpp" },
  { id: "python", label: "Python", filename: "main.py" }
];

export function getSolveTemplate(language: CodeLanguage, problemId: DsaProblem["id"]): string {
  if (language === "python") {
    if (problemId === "two-sum") {
      return [
        "def solve(nums, target):",
        "    # Return two indices whose values add up to target.",
        "    return []",
        ""
      ].join("\n");
    }

    if (problemId === "valid-parentheses") {
      return [
        "def solve(s):",
        "    # Return True when brackets are valid, else False.",
        "    return False",
        ""
      ].join("\n");
    }

    if (problemId === "longest-substring-no-repeat") {
      return [
        "def solve(s):",
        "    # Return the maximum length of a substring with unique characters.",
        "    return 0",
        ""
      ].join("\n");
    }

    return [
      "def solve(lists):",
      "    # Return one merged sorted list.",
      "    return []",
      ""
    ].join("\n");
  }

  if (problemId === "two-sum") {
    return [
      "vector<int> solve(vector<int> nums, int target) {",
      "    // Return two indices whose values add up to target.",
      "    return {};",
      "}",
      ""
    ].join("\n");
  }

  if (problemId === "valid-parentheses") {
    return [
      "bool solve(string s) {",
      "    // Return true when brackets are valid, else false.",
      "    return false;",
      "}",
      ""
    ].join("\n");
  }

  if (problemId === "longest-substring-no-repeat") {
    return [
      "int solve(string s) {",
      "    // Return the maximum length of a substring with unique characters.",
      "    return 0;",
      "}",
      ""
    ].join("\n");
  }

  return [
    "vector<int> solve(vector<vector<int>> lists) {",
    "    // Return one merged sorted list.",
    "    return {};",
    "}",
    ""
  ].join("\n");
}
