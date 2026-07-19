import { DsaProblem, LastProblemResponse, SignInResponse } from "../types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:4000";

export async function signIn(email: string, password: string): Promise<SignInResponse> {
  const response = await fetch(`${API_BASE_URL}/api/auth/signin`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      email: email.trim(),
      password
    })
  });

  if (!response.ok) {
    throw new Error("Unable to sign in. Please check your credentials and retry.");
  }

  return (await response.json()) as SignInResponse;
}

export async function persistLastProblem(
  token: string,
  problemId: DsaProblem["id"]
): Promise<LastProblemResponse> {
  const response = await fetch(`${API_BASE_URL}/api/users/me/last-problem`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify({ problemId })
  });

  if (!response.ok) {
    throw new Error("Failed to save progress");
  }

  return (await response.json()) as LastProblemResponse;
}
