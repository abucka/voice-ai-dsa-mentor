import { useEffect, useState } from "react";
import CodeEditorPanel from "./CodeEditorPanel";
import TutorHelpPanel from "./TutorHelpPanel";
import { CODE_LANGUAGES, getSolveTemplate } from "../constants/codeTemplates";
import { DsaProblem } from "../types";
import { PROBLEMS } from "../constants/problems";
import { runCode } from "../services/codeRunner";
import { submitCode } from "../services/codeSubmitter";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:4000";

type ProblemWorkspaceProps = {
  signedInEmail: string;
  currentProblem: DsaProblem;
  currentProblemIndex: number;
  totalProblems: number;
  onProblemChange: (problemId: DsaProblem["id"]) => Promise<void>;
  onSignOut: () => void;
};

export default function ProblemWorkspace({
  signedInEmail,
  currentProblem,
  currentProblemIndex,
  totalProblems,
  onProblemChange,
  onSignOut
}: ProblemWorkspaceProps) {
  const [code, setCode] = useState<string>("");
  const [runOutput, setRunOutput] = useState("");
  const [isRunning, setIsRunning] = useState(false);
  const [isSolved, setisSolved] = useState(false);
  const [submitOutput, setSubmitOutput] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const language = "python" as const;
  const filename = CODE_LANGUAGES[0]?.filename ?? "main.py";
  const progressPercent = Math.min(100, Math.max(0, (currentProblemIndex / totalProblems) * 100));

  async function handlePreviousProblem() {
    const index = PROBLEMS.findIndex((problem) => problem.id === currentProblem.id);
    const previous = PROBLEMS[(index - 1 + PROBLEMS.length) % PROBLEMS.length];
    await onProblemChange(previous.id);
  }

  async function handleNextProblem() {
    const index = PROBLEMS.findIndex((problem) => problem.id === currentProblem.id);
    const next = PROBLEMS[(index + 1) % PROBLEMS.length];
    await onProblemChange(next.id);
  }

  useEffect(() => {
    fetchSolution();
    setRunOutput("");
    setIsRunning(false);
    setisSolved(false);
    setSubmitOutput("");
    setIsSubmitting(false);
  }, [currentProblem.id]);

  async function fetchSolution() {

      const response = await fetch(
        `${API_BASE_URL}/api/problems/${currentProblem.id}/solution`
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Failed to fetch solution");
      }
      
      data.solution === "" ? setCode(getSolveTemplate(currentProblem.id)) : setCode(data.solution);
      setisSolved(data.is_solved);

  }

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
        //`Exit code: ${result.exitCode}`,
        result.timedOut ? "Timed out: yes" : "Timed out: no",
        "",
        "Sample test input:",
        result.input || "(empty)",
        "",
        "Expected output:",
        result.expectedOutput || "(empty)",
        "",
        "Your output:",
        result.stdout || "(empty)",
        "",
        result.stderr
      ].join("\n");

      setRunOutput(outputText);
    } catch (error) {
      setRunOutput(error instanceof Error ? error.message : "Unable to run code.");
    } finally {
      setIsRunning(false);
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
      result.passed ? setisSolved(true) : setisSolved(false);
      
    } catch (error) {
      setSubmitOutput(error instanceof Error ? error.message : "Unable to submit code.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className="panel workspace">
      <div className="workspaceHeader workspaceHeaderWide">
        <div>
          <p className="eyebrow">Welcome back{signedInEmail ? `, ${signedInEmail}` : ""}</p>
          <h2>Practice workspace</h2>
        </div>
        <div className="workspaceHeaderActions">
          <button type="button" className="ghost" onClick={() => void handlePreviousProblem()}>
            Previous problem
          </button>
          <button type="button" className="ghost" onClick={() => void handleNextProblem()}>
            Next problem
          </button>
          <button type="button" className="ghost" onClick={onSignOut}>
            Sign out
          </button>
        </div>
      </div>

      <div className="workspaceInsights" aria-label="Current learning context">
        <p className="workspaceMetaText">Problem {currentProblemIndex} of {totalProblems}</p>
        <p className="workspaceMetaText">Language: Python</p>
      </div>
      <div className="progressTrack" role="progressbar" aria-valuenow={currentProblemIndex} aria-valuemin={1} aria-valuemax={totalProblems}>
        <span style={{ width: `${progressPercent}%` }} />
      </div>
      <div className="workspaceFlow">
        <article className="problemCard">
          <div className="workspaceInsights">
            <div className="problemMeta">
              <span>{currentProblem.difficulty}</span>
              <span>{currentProblem.topic}</span>
            </div>
          {isSolved ? (
            <div className="problemMeta green">
              <span>✓ Solved</span>
            </div>
          ) : (
            <div className="problemMeta red">
              <span>✗ Not solved</span>
            </div>
          )}
          </div>
          <h3>{currentProblem.title}</h3>
          <p>{currentProblem.summary}</p>
        </article>

        <div className="workspaceMainGrid">
          <div className="workspacePrimaryColumn">
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
          </div>

          <div className="workspaceSecondaryColumn">
            <TutorHelpPanel code={code} problemId={currentProblem.id} />
          </div>
        </div>

        <div className="workspaceBottomSection">
          <div className="actions">
            <button type="button" className="primary" onClick={handleSubmitCode} disabled={isSubmitting}>
              {isSubmitting ? "Submitting..." : "Submit"}
            </button>
          </div>
          <section className="outputPanel" aria-live="polite">
            <p className="editorLabel">Submission</p>
            <pre className="outputBox">{submitOutput || "Submit your code to check it against sample tests."}</pre>
          </section>
        </div>
      </div>

    </section>
  );
}
