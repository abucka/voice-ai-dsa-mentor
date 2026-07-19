import { useMemo, useState } from "react";
import CodeEditorPanel from "./CodeEditorPanel";
import { CODE_LANGUAGES, getStarterCode } from "../constants/codeTemplates";
import { DsaProblem, CodeLanguage, MentorMode } from "../types";
import { runCode } from "../services/codeRunner";

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
  const [language, setLanguage] = useState<CodeLanguage>("cpp");
  const [codeByLanguage, setCodeByLanguage] = useState<Record<CodeLanguage, string>>({
    cpp: getStarterCode("cpp"),
    python: getStarterCode("python")
  });
  const [runOutput, setRunOutput] = useState("");
  const [isRunning, setIsRunning] = useState(false);

  const code = codeByLanguage[language];
  const filename = useMemo(() => CODE_LANGUAGES.find((entry) => entry.id === language)?.filename ?? "main.cpp", [language]);

  function handleLanguageChange(nextLanguage: CodeLanguage) {
    setLanguage(nextLanguage);
    setCodeByLanguage((current) => ({
      ...current,
      [nextLanguage]: current[nextLanguage] || getStarterCode(nextLanguage)
    }));
  }

  function handleReset() {
    setCodeByLanguage((current) => ({
      ...current,
      [language]: getStarterCode(language)
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
      const result = await runCode(language, code);
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

        <label htmlFor="mode">Mentor mode</label>
        <select id="mode" value={mode} onChange={(event) => onModeChange(event.target.value as MentorMode)}>
          {modes.map((currentMode) => (
            <option key={currentMode} value={currentMode}>
              {currentMode}
            </option>
          ))}
        </select>
        <p className="modeCopy">{subtitle}</p>

        <div className="actions">
          <button type="button" className="primary">
            Resume Problem
          </button>
          <button type="button" className="ghost" onClick={onNextProblem}>
            Simulate Next Problem
          </button>
        </div>
        <p className="statusRow">{isSavingProgress ? "Saving progress..." : "Progress synced"}</p>
      </article>

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
    </section>
  );
}
