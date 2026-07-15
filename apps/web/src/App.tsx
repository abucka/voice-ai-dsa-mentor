import { useMemo, useState } from "react";

type MentorMode = "explain" | "interview" | "hints-only";

const MODES: MentorMode[] = ["explain", "interview", "hints-only"];

export default function App() {
  const [mode, setMode] = useState<MentorMode>("explain");

  const subtitle = useMemo(() => {
    if (mode === "interview") return "Interview simulation with strict feedback";
    if (mode === "hints-only") return "Nudges only, no full solution spoilers";
    return "Concept-first guidance with examples and tradeoffs";
  }, [mode]);

  return (
    <main className="page">
      <section className="card">
        <h1>Voice AI DSA Mentor</h1>
        <p>{subtitle}</p>

        <label htmlFor="mode">Mentor mode</label>
        <select id="mode" value={mode} onChange={(e) => setMode(e.target.value as MentorMode)}>
          {MODES.map((m) => (
            <option key={m} value={m}>
              {m}
            </option>
          ))}
        </select>

        <button type="button" disabled>
          Start voice session (coming next)
        </button>
      </section>
    </main>
  );
}
