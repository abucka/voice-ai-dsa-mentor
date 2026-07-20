import { useEffect, useState } from "react";
import CodeEditorPanel from "./CodeEditorPanel";
import { CODE_LANGUAGES, getSolveTemplate } from "../constants/codeTemplates";
import { DsaProblem, MentorMode } from "../types";
import { runCode } from "../services/codeRunner";
import { askTutor } from "../services/helpTutor";
import { submitCode } from "../services/codeSubmitter";

type ProblemWorkspaceProps = {
  signedInEmail: string;
  currentProblem: DsaProblem;
  mode: MentorMode;
  modes: MentorMode[];
  subtitle: string;
  isSavingProgress: boolean;
  onModeChange: (mode: MentorMode) => void;
  onNextProblem: () => Promise<void>;
  onSignOut: () => void;
};

export default function ProblemWorkspace({
  signedInEmail,
  currentProblem,
  mode,
  modes,
  subtitle,
  isSavingProgress,
  onModeChange,
  onNextProblem,
  onSignOut
}: ProblemWorkspaceProps) {
  const [code, setCode] = useState<string>(() => getSolveTemplate(currentProblem.id));
  const [runOutput, setRunOutput] = useState("");
  const [isRunning, setIsRunning] = useState(false);
  const [helpQuestion, setHelpQuestion] = useState("");
  const [helpAnswer, setHelpAnswer] = useState("");
  const [helpStatus, setHelpStatus] = useState("");
  const [isAskingHelp, setIsAskingHelp] = useState(false);
  const [submitOutput, setSubmitOutput] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const language = "python" as const;
  const filename = CODE_LANGUAGES[0]?.filename ?? "main.py";

  useEffect(() => {
    setCode(getSolveTemplate(currentProblem.id));
    setRunOutput("");
    setIsRunning(false);
    setHelpQuestion("");
    setHelpAnswer("");
    setHelpStatus("");
    setIsAskingHelp(false);
    setSubmitOutput("");
    setIsSubmitting(false);
  }, [currentProblem.id]);

  function handleReset() {
    setCode(getSolveTemplate(currentProblem.id));
  }

  function handleLanguageChange() {
    // Python is the only supported language now.
  }

  function handleCodeChange(nextCode: string) {
    setCode(nextCode);
  }

  async function handleRunCode() {
    setIsRunning(true);
    setRunOutput("");

    try {
      const result = await runCode(currentProblem.id, language, code);
      const outputText = [
        `Exit code: ${result.exitCode}`,
        result.timedOut ? "Timed out: yes" : "Timed out: no",
        "",
        "STDOUT",
        result.stdout || "(empty)",
        "",
        "STDERR",
        result.stderr || "(empty)"
      ].join("\n");

      setRunOutput(outputText);
    } catch (error) {
      setRunOutput(error instanceof Error ? error.message : "Unable to run code.");
    } finally {
      setIsRunning(false);
    }
  }

  async function handleAskTutor() {
    const trimmedQuestion = helpQuestion.trim();
    if (!trimmedQuestion) {
      setHelpStatus("Please type a question for the tutor.");
      return;
    }

    setIsAskingHelp(true);
    setHelpStatus("Asking the tutor...");
    setHelpAnswer("");

    try {
      const result = await askTutor(currentProblem.id, language, code, trimmedQuestion, mode);
      setHelpAnswer(result.answer);
      //setHelpStatus(result.voiceUsed ? `Answered with ElevenLabs voice ${result.voiceUsed}.` : "Answered as text only.");

      if (result.answer) {
        setHelpStatus(result.answer);
      }
    } catch (error) {
      setHelpStatus(error instanceof Error ? error.message : "Unable to get tutor help.");
    } finally {
      setIsAskingHelp(false);
    }
  }

  async function handleSubmitCode() {
    setIsSubmitting(true);
    setSubmitOutput("");

    try {
      const result = await submitCode(currentProblem.id, language, code);
      const output = [
        result.passed ? "All sample tests passed." : "Some sample tests failed.",
        `Passed ${result.passedTests}/${result.totalTests} sample tests.`,
        result.note ? `Note: ${result.note}` : "",
        "",
        ...result.results.flatMap((test, index) => [
          `Test ${index + 1}: ${test.passed ? "passed" : "failed"}`,
          `Input: ${test.input.trim() || "(empty)"}`,
          `Expected: ${test.expectedOutput.trim() || "(empty)"}`,
          `Actual: ${test.actualOutput.trim() || "(empty)"}`,
          test.stderr ? `Stderr: ${test.stderr.trim()}` : "",
          test.reason ? `Reason: ${test.reason}` : "",
          ""
        ])
      ]
        .filter((line) => line !== "")
        .join("\n");

      setSubmitOutput(output || "Submission completed.");
    } catch (error) {
      setSubmitOutput(error instanceof Error ? error.message : "Unable to submit code.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className="panel workspace">
      <div className="workspaceHeader">
        <p className="eyebrow">Welcome back{signedInEmail ? `, ${signedInEmail}` : ""}</p>
        <button type="button" className="ghost" onClick={onSignOut}>
          Sign out
        </button>
      </div>

      <h2>Your last DSA problem</h2>
      <article className="problemCard">
        <div className="problemMeta">
          <span>{currentProblem.difficulty}</span>
          <span>{currentProblem.topic}</span>
        </div>
        <h3>{currentProblem.title}</h3>
        <p>{currentProblem.summary}</p>

        <CodeEditorPanel
          language={language}
          filename={filename}
          code={code}
          onLanguageChange={handleLanguageChange}
          onCodeChange={handleCodeChange}
          onReset={handleReset}
        />
        <div className="runControls">
          <button type="button" className="primary" onClick={handleRunCode} disabled={isRunning}>
            {isRunning ? "Running..." : "Run Code"}
          </button>
        </div>
        <section className="outputPanel" aria-live="polite">
          <p className="editorLabel">Output</p>
          <pre className="outputBox">{runOutput || "Run your code to see output here."}</pre>
        </section>

        <section className="helpPanel">
          <div className="helpHeaderRow">
            <p className="editorLabel">Ask AI Tutor</p>
            <button type="button" className="ghost helpButton" onClick={handleAskTutor} disabled={isAskingHelp}>
              {isAskingHelp ? "Asking..." : "Help"}
            </button>
          </div>
          <label htmlFor="helpQuestion" className="srOnly">
            Ask the AI tutor for help
          </label>
          <textarea
            id="helpQuestion"
            className="helpTextarea"
            value={helpQuestion}
            onChange={(event) => setHelpQuestion(event.target.value)}
            placeholder="What part are you stuck on?"
            rows={3}
          />
          <p className="statusRow">{helpStatus || "Ask a question and the tutor will reply here."}</p>
        </section>

        <div className="actions">
          <button type="button" className="primary" onClick={handleSubmitCode} disabled={isSubmitting}>
            {isSubmitting ? "Submitting..." : "Submit"}
          </button>
          <button type="button" className="ghost" onClick={onNextProblem}>
            Next Problem
          </button>
        </div>
        <section className="outputPanel" aria-live="polite">
          <p className="editorLabel">Submission</p>
          <pre className="outputBox">{submitOutput || "Submit your code to check it against sample tests."}</pre>
        </section>
        <p className="statusRow">{isSavingProgress ? "Saving progress..." : "Progress synced"}</p>
      </article>

    </section>
  );
}
