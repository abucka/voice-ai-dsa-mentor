import { FormEvent, useMemo, useState } from "react";
import LandingScreen from "./components/LandingScreen";
import ProblemWorkspace from "./components/ProblemWorkspace";
import SignInScreen from "./components/SignInScreen";
import { REQUIRE_SIGNIN_PARAM } from "./config/appConfig";
import { PROBLEMS } from "./constants/problems";
import { persistLastProblem, signIn } from "./services/authService";
import { getInitialProblemId, saveProblemIdLocally } from "./services/progressStorage";
import { DsaProblem, Screen } from "./types";

export default function App() {
  const [screen, setScreen] = useState<Screen>("landing");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [signedInEmail, setSignedInEmail] = useState("");
  const [authToken, setAuthToken] = useState("");
  const [error, setError] = useState("");
  const [isSigningIn, setIsSigningIn] = useState(false);
  const [isSavingProgress, setIsSavingProgress] = useState(false);
  const [lastProblemId, setLastProblemId] = useState<number>(getInitialProblemId);

  const currentProblem = useMemo(
    () => PROBLEMS.find((problem) => problem.id === lastProblemId) ?? PROBLEMS[0],
    [lastProblemId]
  );

  const currentProblemIndex = useMemo(() => {
    const index = PROBLEMS.findIndex((problem) => problem.id === currentProblem.id);
    return index >= 0 ? index + 1 : 1;
  }, [currentProblem.id]);

  function handleStartLearning() {
    setScreen(REQUIRE_SIGNIN_PARAM ? "signin" : "problem");
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

  function saveProgressLocal(problemId: number) {
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

  async function goToPreviousProblem() {
    const index = PROBLEMS.findIndex((problem) => problem.id === currentProblem.id);
    const previous = PROBLEMS[(index - 1 + PROBLEMS.length) % PROBLEMS.length];
    await saveProgress(previous.id);
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
          currentProblemIndex={currentProblemIndex}
          totalProblems={PROBLEMS.length}
          isSavingProgress={isSavingProgress}
          onPreviousProblem={goToPreviousProblem}
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
