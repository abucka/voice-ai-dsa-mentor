import { useEffect, useRef, useState } from "react";
import { askTutor } from "../services/helpTutor";
import { transcribeVoice } from "../services/voiceTranscriber";

type TutorHelpPanelProps = {
  code: string;
  problemId: number;
};

export default function TutorHelpPanel({ code, problemId }: TutorHelpPanelProps) {
  const [helpQuestion, setHelpQuestion] = useState("");
  const [helpAnswer, setHelpAnswer] = useState("");
  const [helpStatus, setHelpStatus] = useState("");
  const [tutorMessages, setTutorMessages] = useState<Array<{ role: "user" | "assistant"; content: string }>>([]);
  const [isAskingHelp, setIsAskingHelp] = useState(false);
  const [isRecordingVoice, setIsRecordingVoice] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const audioChunksRef = useRef<BlobPart[]>([]);

  useEffect(() => {
    setHelpQuestion("");
    setHelpAnswer("");
    setHelpStatus("");
    setTutorMessages([]);
    setIsAskingHelp(false);
    setIsRecordingVoice(false);
    mediaRecorderRef.current = null;
    mediaStreamRef.current?.getTracks().forEach((track) => track.stop());
    mediaStreamRef.current = null;
    audioChunksRef.current = [];
  }, [problemId]);

  async function handleAskTutor(questionOverride?: string) {
    const trimmedQuestion = (questionOverride ?? helpQuestion).trim();
    if (!trimmedQuestion) {
      setHelpStatus("Please type a question for the tutor.");
      return;
    }

    setIsAskingHelp(true);
    setHelpStatus("Asking the tutor...");
    setHelpAnswer("");
    setTutorMessages((previous) => [...previous, { role: "user", content: trimmedQuestion }]);

    try {
      const result = await askTutor(problemId, "python", code, trimmedQuestion, "explain");
      setTutorMessages((previous) => [...previous, { role: "assistant", content: result.answer }]);
      setHelpAnswer(result.answer);
      setHelpStatus("Tutor answered.");
    } catch (error) {
      setHelpStatus(error instanceof Error ? error.message : "Unable to get tutor help.");
    } finally {
      setIsAskingHelp(false);
    }
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

  return (
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
      {helpAnswer && (
        <div className="helpAnswerBox">
          <p className="editorLabel">Tutor response</p>
          <pre className="outputBox tutorAnswerBox">{helpAnswer}</pre>
        </div>
      )}
    </section>
  );
}
