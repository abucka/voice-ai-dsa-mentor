import { CodeLanguage, DsaProblem } from "../types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:4000";

export type RunCodeResponse = {
  language: CodeLanguage;
  stdout: string;
  stderr: string;
  exitCode: number;
  timedOut: boolean;
};

export async function runCode(
  problemId: DsaProblem["id"],
  language: CodeLanguage,
  code: string
): Promise<RunCodeResponse> {
  const response = await fetch(`${API_BASE_URL}/api/code/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ problemId, language, code })
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || "Unable to run code right now.");
  }

  return (await response.json()) as RunCodeResponse;
}
