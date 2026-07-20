import { useEffect, useMemo, useState } from "react";
import CodeEditorPanel from "./CodeEditorPanel";
import { CODE_LANGUAGES, getSolveTemplate } from "../constants/codeTemplates";
import { DsaProblem, CodeLanguage, MentorMode } from "../types";
import { runCode } from "../services/codeRunner";
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
  function buildTemplates(problemId: DsaProblem["id"]): Record<CodeLanguage, string> {
    return {
      cpp: getSolveTemplate("cpp", problemId),
      python: getSolveTemplate("python", problemId)
    };
  }

  const [language, setLanguage] = useState<CodeLanguage>("cpp");
  const [codeByLanguage, setCodeByLanguage] = useState<Record<CodeLanguage, string>>(() =>
    buildTemplates(currentProblem.id)
  );
  const [runOutput, setRunOutput] = useState("");
  const [isRunning, setIsRunning] = useState(false);
  const [submitOutput, setSubmitOutput] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const code = codeByLanguage[language];
  const filename = useMemo(() => CODE_LANGUAGES.find((entry) => entry.id === language)?.filename ?? "main.cpp", [language]);

  useEffect(() => {
    setCodeByLanguage(buildTemplates(currentProblem.id));
  }, [currentProblem.id]);

  function handleLanguageChange(nextLanguage: CodeLanguage) {
    setLanguage(nextLanguage);
    setCodeByLanguage((current) => ({
      ...current,
      [nextLanguage]: current[nextLanguage] || getSolveTemplate(nextLanguage, currentProblem.id)
    }));
  }

  function handleReset() {
    setCodeByLanguage((current) => ({
      ...current,
      [language]: getSolveTemplate(language, currentProblem.id)
    }));
  }

  function handleCodeChange(nextCode: string) {
    setCodeByLanguage((current) => ({
      ...current,
      [language]: nextCode
    }));
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
