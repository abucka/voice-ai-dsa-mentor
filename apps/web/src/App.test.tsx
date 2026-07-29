import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import App from "./App";
import * as authService from "./services/authService";

vi.mock("./config/appConfig", () => ({ REQUIRE_SIGNIN_PARAM: true }));

vi.mock("@monaco-editor/react", () => ({
  default: ({ value, onChange }: { value?: string; onChange?: (value: string) => void }) => (
    <textarea aria-label="code-editor" value={value ?? ""} onChange={(event) => onChange?.(event.target.value)} />
  )
}));

vi.mock("./services/authService", () => ({
  signIn: vi.fn(),
  persistLastProblem: vi.fn().mockResolvedValue({ email: "student@example.com", lastProblemId: 1 })
}));

vi.mock("./services/progressStorage", () => ({
  getInitialProblemId: () => 1,
  saveProblemIdLocally: vi.fn()
}));

vi.mock("./services/codeRunner", () => ({ runCode: vi.fn() }));
vi.mock("./services/helpTutor", () => ({ askTutor: vi.fn() }));
vi.mock("./services/voiceTranscriber", () => ({ transcribeVoice: vi.fn() }));
vi.mock("./services/codeSubmitter", () => ({ submitCode: vi.fn() }));

describe("App", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the landing experience and transitions to sign-in", () => {
    render(<App />);

    expect(screen.getByText(/Train for interviews with an AI pair mentor/i)).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: /start a practice session/i }));

    expect(screen.getByText(/Sign in to continue/i)).toBeTruthy();
  });

  it("signs in successfully and shows the practice workspace", async () => {
    vi.mocked(authService.signIn).mockResolvedValue({
      token: "demo-token",
      email: "student@example.com",
      lastProblemId: 1
    });

    render(<App />);

    fireEvent.click(screen.getByRole("button", { name: /start a practice session/i }));
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: "student@example.com" } });
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: "secret" } });
    fireEvent.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(screen.getByText(/Practice workspace/i)).toBeTruthy();
    });

    expect(authService.signIn).toHaveBeenCalledWith("student@example.com", "secret");
  });
});
