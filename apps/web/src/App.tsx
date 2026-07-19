import { FormEvent, useMemo, useState } from "react";
import LandingScreen from "./components/LandingScreen";
import ProblemWorkspace from "./components/ProblemWorkspace";
import SignInScreen from "./components/SignInScreen";
import { MODES, PROBLEMS } from "./constants/problems";
import { persistLastProblem, signIn } from "./services/authService";
import { getInitialProblemId, saveProblemIdLocally } from "./services/progressStorage";
import { DsaProblem, MentorMode, Screen } from "./types";

export default function App() {
  const [screen, setScreen] = useState<Screen>("landing");
  const [mode, setMode] = useState<MentorMode>("explain");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [signedInEmail, setSignedInEmail] = useState("");
  const [authToken, setAuthToken] = useState("");
  const [error, setError] = useState("");
  const [isSigningIn, setIsSigningIn] = useState(false);
  const [isSavingProgress, setIsSavingProgress] = useState(false);
  const [lastProblemId, setLastProblemId] = useState<string>(getInitialProblemId);

  const subtitle = useMemo(() => {
    if (mode === "interview") return "Interview simulation with strict feedback";
    if (mode === "hints-only") return "Nudges only, no full solution spoilers";
    return "Concept-first guidance with examples and tradeoffs";
  }, [mode]);

  const currentProblem = useMemo(
    () => PROBLEMS.find((problem) => problem.id === lastProblemId) ?? PROBLEMS[0],
    [lastProblemId]
  );

  function handleStartLearning() {
    setScreen("signin");
    setError("");
  }

  async function handleSignIn(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!email.trim() || !password.trim()) {
      setError("Please enter both email and password.");
      return;
    }

    setIsSigningIn(true);
    setError("");

    try {
      const data = await signIn(email, password);
      setAuthToken(data.token);
      setSignedInEmail(data.email);
      saveProgressLocal(data.lastProblemId);
      setScreen("problem");
    } catch {
      setError("Unable to sign in right now. Please try again in a moment.");
    } finally {
      setIsSigningIn(false);
    }
  }

  function saveProgressLocal(problemId: string) {
    setLastProblemId(problemId);
    saveProblemIdLocally(problemId);
  }

  async function saveProgress(problemId: DsaProblem["id"]) {
    saveProgressLocal(problemId);

    if (!authToken) return;

    setIsSavingProgress(true);
    try {
      const data = await persistLastProblem(authToken, problemId);
      saveProgressLocal(data.lastProblemId);
    } catch {
      setError("Signed in, but saving progress failed. We kept progress locally.");
    } finally {
      setIsSavingProgress(false);
    }
  }

  async function goToNextProblem() {
    const index = PROBLEMS.findIndex((problem) => problem.id === currentProblem.id);
    const next = PROBLEMS[(index + 1) % PROBLEMS.length];
    await saveProgress(next.id);
  }

  return (
    <main className="page">
      {screen === "landing" && <LandingScreen onStartLearning={handleStartLearning} />}

      {screen === "signin" && (
        <SignInScreen
          email={email}
          password={password}
          error={error}
          isSigningIn={isSigningIn}
          onEmailChange={setEmail}
          onPasswordChange={setPassword}
          onSignIn={handleSignIn}
          onBack={() => setScreen("landing")}
        />
      )}

      {screen === "problem" && (
        <ProblemWorkspace
          signedInEmail={signedInEmail}
          currentProblem={currentProblem}
          mode={mode}
          modes={MODES}
          subtitle={subtitle}
          isSavingProgress={isSavingProgress}
          onModeChange={setMode}
          onNextProblem={goToNextProblem}
          onSignOut={() => {
            setAuthToken("");
            setSignedInEmail("");
            setPassword("");
            setScreen("landing");
          }}
        />
      )}
    </main>
  );
}
