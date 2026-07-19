import { CodeLanguage, SubmitCodeResponse, DsaProblem } from "../types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:4000";

export async function submitCode(
  problemId: DsaProblem["id"],
  language: CodeLanguage,
  code: string
): Promise<SubmitCodeResponse> {
  const response = await fetch(`${API_BASE_URL}/api/code/submit`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ problemId, language, code })
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || "Unable to submit code right now.");
  }

  return (await response.json()) as SubmitCodeResponse;
}
