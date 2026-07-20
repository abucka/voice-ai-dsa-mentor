import Editor from "@monaco-editor/react";
import { CodeLanguage } from "../types";

type CodeEditorPanelProps = {
  language: CodeLanguage;
  filename: string;
  code: string;
  onLanguageChange: (language: CodeLanguage) => void;
  onCodeChange: (code: string) => void;
  onReset: () => void;
};

export default function CodeEditorPanel({
  language,
  filename,
  code,
  onLanguageChange,
  onCodeChange,
  onReset
}: CodeEditorPanelProps) {
  return (
    <section className="editorPanel">
      <div className="editorToolbar">
        <div>
          <p className="editorLabel">Code editor</p>
          <p className="editorHint">Write your solution in {language === "cpp" ? "C++" : "Python"}.</p>
        </div>

        <div className="editorControls">
          <label className="srOnly" htmlFor="language">
            Language
          </label>
          <select id="language" value={language} onChange={(event) => onLanguageChange(event.target.value as CodeLanguage)}>
            <option value="cpp">C++</option>
            <option value="python">Python</option>
          </select>
          <button type="button" className="ghost editorReset" onClick={onReset}>
            Reset
          </button>
        </div>
      </div>

      <div className="editorFilename">{filename}</div>
      <Editor
        height="340px"
        defaultLanguage={language}
        language={language}
        theme="vs-light"
        value={code}
        onChange={(value) => onCodeChange(value ?? "")}
        options={{
          fontSize: 14,
          minimap: { enabled: false },
          wordWrap: "on",
          scrollBeyondLastLine: false,
          automaticLayout: true
        }}
      />
    </section>
  );
}
