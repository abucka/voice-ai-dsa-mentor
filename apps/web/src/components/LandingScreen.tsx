type LandingScreenProps = {
  onStartLearning: () => void;
};

export default function LandingScreen({ onStartLearning }: LandingScreenProps) {
  return (
    <section className="panel hero">
      <p className="eyebrow">Voice AI DSA Mentor</p>
      <h1>Train for interviews with an AI mentor.</h1>
      <p className="lead">
        Build momentum in focused daily sessions with instant code feedback, voice help, and guided problem solving.
      </p>

      <div className="heroHighlights" aria-label="Core learning benefits">
        <article className="heroHighlightCard">
          <p className="heroHighlightLabel">Voice-first help</p>
          <p className="heroHighlightText">Ask questions by typing or speaking when you are stuck.</p>
        </article>
        <article className="heroHighlightCard">
          <p className="heroHighlightLabel">Interview-ready drills</p>
          <p className="heroHighlightText">Practice problem patterns with realistic constraints and feedback.</p>
        </article>
        <article className="heroHighlightCard">
          <p className="heroHighlightLabel">Progress memory</p>
          <p className="heroHighlightText">Return exactly where you left off and keep your streak alive.</p>
        </article>
      </div>

      <button type="button" className="primary" onClick={onStartLearning}>
        Start a Practice Session
      </button>
      <p className="modeCopy">No setup friction. Open, pick a problem, and start coding.</p>
    </section>
  );
}
