import { DsaProblem, HelpTutorResponse, MentorMode } from "../types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:4000";

export async function askTutor(
  problemId: DsaProblem["id"],
  language: "python",
  code: string,
  question: string,
  mode: MentorMode
): Promise<HelpTutorResponse> {
  const response = await fetch(`${API_BASE_URL}/api/help`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ problemId, language, code, question, mode })
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || "Unable to get tutor help right now.");
  }

  return (await response.json()) as HelpTutorResponse;
}
