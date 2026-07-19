type LandingScreenProps = {
  onStartLearning: () => void;
};

export default function LandingScreen({ onStartLearning }: LandingScreenProps) {
  return (
    <section className="panel hero">
      <p className="eyebrow">Voice AI DSA Mentor</p>
      <h1>Learn DSA with guided practice that picks up where you stopped.</h1>
      <p className="lead">
        Choose your mentoring style, resume your latest problem, and keep momentum in short daily sessions.
      </p>
      <button type="button" className="primary" onClick={onStartLearning}>
        Start Learning
      </button>
    </section>
  );
}
