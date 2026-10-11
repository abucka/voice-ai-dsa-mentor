import { useEffect, useRef, useState } from "react";
import CodeEditorPanel from "./CodeEditorPanel";
import { CODE_LANGUAGES, getSolveTemplate } from "../constants/codeTemplates";
import { DsaProblem } from "../types";
import { runCode } from "../services/codeRunner";
import { buildTutorWebSocketUrl } from "../services/helpTutor";
import { transcribeVoice } from "../services/voiceTranscriber";
import { submitCode } from "../services/codeSubmitter";

type ProblemWorkspaceProps = {
  signedInEmail: string;
  currentProblem: DsaProblem;
  currentProblemIndex: number;
  totalProblems: number;
  isSavingProgress: boolean;
  onPreviousProblem: () => Promise<void>;
  onNextProblem: () => Promise<void>;
  onSignOut: () => void;
};

export default function ProblemWorkspace({
  signedInEmail,
  currentProblem,
  currentProblemIndex,
  totalProblems,
  isSavingProgress,
  onPreviousProblem,
  onNextProblem,
  onSignOut
}: ProblemWorkspaceProps) {
  const [code, setCode] = useState<string>(() => getSolveTemplate(currentProblem.id));
  const [runOutput, setRunOutput] = useState("");
  const [isRunning, setIsRunning] = useState(false);
  const [helpQuestion, setHelpQuestion] = useState("");
  const [helpAnswer, setHelpAnswer] = useState("");
  const [helpStatus, setHelpStatus] = useState("");
  const [tutorMessages, setTutorMessages] = useState<Array<{ role: "user" | "assistant"; content: string }>>([]);
  const [isAskingHelp, setIsAskingHelp] = useState(false);
  const [isRecordingVoice, setIsRecordingVoice] = useState(false);
  const [submitOutput, setSubmitOutput] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const audioChunksRef = useRef<BlobPart[]>([]);
  const tutorSocketRef = useRef<WebSocket | null>(null);

  const language = "python" as const;
  const filename = CODE_LANGUAGES[0]?.filename ?? "main.py";
  const progressPercent = Math.min(100, Math.max(0, (currentProblemIndex / totalProblems) * 100));

  useEffect(() => {
    setCode(getSolveTemplate(currentProblem.id));
    setRunOutput("");
    setIsRunning(false);
    setHelpQuestion("");
    setHelpAnswer("");
    setHelpStatus("");
    setTutorMessages([]);
    setIsAskingHelp(false);
    setIsRecordingVoice(false);
    setSubmitOutput("");
    setIsSubmitting(false);
    mediaRecorderRef.current = null;
    mediaStreamRef.current?.getTracks().forEach((track) => track.stop());
    mediaStreamRef.current = null;
    audioChunksRef.current = [];

    const socket = new WebSocket(buildTutorWebSocketUrl());
    tutorSocketRef.current = socket;

    socket.addEventListener("open", () => {
      setHelpStatus("Tutor is ready.");
    });

    socket.addEventListener("message", (event) => {
      try {
        const payload = JSON.parse(event.data) as { type?: string; message?: string; content?: string; role?: string };
        if (payload.type === "message") {
          const content = payload.content?.trim() || "";
          if (content) {
            setTutorMessages((previous) => [...previous, { role: "assistant", content }]);
            setHelpAnswer(content);
            setHelpStatus("Tutor answered.");
          }
        } else if (payload.type === "ready") {
          setHelpStatus(payload.message || "Tutor is ready.");
        } else if (payload.type === "error") {
          setHelpStatus(payload.message || "Unable to connect to the tutor.");
        }
      } catch {
        setHelpStatus("Unable to read the tutor response.");
      } finally {
        setIsAskingHelp(false);
      }
    });

    socket.addEventListener("error", () => {
      setHelpStatus("The tutor connection dropped. Please try again.");
      setIsAskingHelp(false);
    });

    return () => {
      socket.close();
      tutorSocketRef.current = null;
    };
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

  async function handleAskTutor(questionOverride?: string) {
    const trimmedQuestion = (questionOverride ?? helpQuestion).trim();
    if (!trimmedQuestion) {
      setHelpStatus("Please type a question for the tutor.");
      return;
    }

    const socket = tutorSocketRef.current;
    setIsAskingHelp(true);
    setHelpStatus("Asking the tutor...");
    setHelpAnswer("");
    setTutorMessages((previous) => [...previous, { role: "user", content: trimmedQuestion }]);

    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(
        JSON.stringify({
          type: "message",
          problemId: currentProblem.id,
          language,
          code,
          question: trimmedQuestion,
          mode: "explain"
        })
      );
      return;
    }

    setHelpStatus("The tutor connection is not ready yet. Please try again.");
    setIsAskingHelp(false);
  }

  async function startVoiceHelp() {
    if (!navigator.mediaDevices?.getUserMedia) {
      setHelpStatus("Your browser does not support microphone recording.");
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      mediaStreamRef.current = stream;
      audioChunksRef.current = [];

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      recorder.onstop = async () => {
        try {
          const blob = new Blob(audioChunksRef.current, { type: recorder.mimeType || "audio/webm" });
          const audioBase64 = await blobToBase64(blob);
          setHelpStatus("Transcribing your voice question...");
          const transcript = await transcribeVoice(audioBase64, blob.type || "audio/webm");
          setHelpQuestion(transcript);
          await handleAskTutor(transcript);
        } catch (error) {
          setHelpStatus(error instanceof Error ? error.message : "Unable to transcribe your voice question.");
        } finally {
          setIsRecordingVoice(false);
          stream.getTracks().forEach((track) => track.stop());
          mediaRecorderRef.current = null;
          mediaStreamRef.current = null;
          audioChunksRef.current = [];
        }
      };

      recorder.start();
      mediaRecorderRef.current = recorder;
      setIsRecordingVoice(true);
      setHelpStatus("Recording... click stop when finished.");
    } catch (error) {
      setHelpStatus(error instanceof Error ? error.message : "Unable to access the microphone.");
    }
  }

  function stopVoiceHelp() {
    mediaRecorderRef.current?.stop();
  }

  function blobToBase64(blob: Blob): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onloadend = () => {
        const result = reader.result;
        if (typeof result !== "string") {
          reject(new Error("Unable to read recorded audio."));
          return;
        }

        const base64 = result.split(",")[1] ?? "";
        resolve(base64);
      };
      reader.onerror = () => reject(new Error("Unable to read recorded audio."));
      reader.readAsDataURL(blob);
    });
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
      <div className="workspaceHeader workspaceHeaderWide">
        <div>
          <p className="eyebrow">Welcome back{signedInEmail ? `, ${signedInEmail}` : ""}</p>
          <h2>Practice workspace</h2>
        </div>
        <div className="workspaceHeaderActions">
          <button type="button" className="ghost" onClick={onPreviousProblem}>
            Previous problem
          </button>
          <button type="button" className="ghost" onClick={onNextProblem}>
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
          <div className="problemMeta">
            <span>{currentProblem.difficulty}</span>
            <span>{currentProblem.topic}</span>
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
            <section className="helpPanel">
              <div className="helpHeaderRow">
                <p className="editorLabel">AI Tutor Coach</p>
                <div className="helpButtonGroup">
                  <button type="button" className="ghost helpButton" onClick={() => void handleAskTutor()} disabled={isAskingHelp || isRecordingVoice}>
                    {isAskingHelp ? "Asking..." : "Help"}
                  </button>
                  <button
                    type="button"
                    className="ghost helpButton"
                    onClick={() => {
                      if (isRecordingVoice) {
                        stopVoiceHelp();
                        return;
                      }

                      void startVoiceHelp();
                    }}
                    disabled={isAskingHelp}
                  >
                    {isRecordingVoice ? "Stop Voice" : "Ask by Voice"}
                  </button>
                </div>
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
                rows={4}
              />
              <p className="statusRow">{helpStatus || "Ask a question and the tutor will reply here."}</p>
              <div className="tutorConversation" aria-live="polite">
                {tutorMessages.length === 0 ? (
                  <div className="tutorEmptyState">Start with a simple question and keep the conversation going.</div>
                ) : (
                  tutorMessages.map((message, index) => (
                    <div key={`${message.role}-${index}`} className={`tutorMessage ${message.role}`}>
                      <strong>{message.role === "user" ? "You" : "Tutor"}</strong>
                      <p>{message.content}</p>
                    </div>
                  ))
                )}
              </div>
              {helpAnswer && (
                <div className="helpAnswerBox">
                  <p className="editorLabel">Latest tutor response</p>
                  <pre className="outputBox tutorAnswerBox">{helpAnswer}</pre>
                </div>
              )}
            </section>
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
