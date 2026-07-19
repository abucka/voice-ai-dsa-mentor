import { DsaProblem, MentorMode } from "../types";

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
    </section>
  );
}
