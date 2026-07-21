import { DsaProblem } from "../types";

export const CODE_LANGUAGES = [
  { id: "python", label: "Python", filename: "main.py" }
];

export function getSolveTemplate(problemId: DsaProblem["id"]): string {
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

  if (problemId === "duplicates") {
    return [
        "def solve(s):",
        "    # Return string without duplicates.",
        "    return s"
    ].join("\n");

  }   
  return [
    "def solve(lists):",
    "    # Return one merged sorted list.",
    "    return []",
    ""
  ].join("\n");
}
