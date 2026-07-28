type LandingScreenProps = {
  onStartLearning: () => void;
};

export default function LandingScreen({ onStartLearning }: LandingScreenProps) {
  return (
    <section className="panel hero">
      <p className="eyebrow">Voice AI DSA Mentor</p>
      <h1>Learn DSA with guided practice.</h1>
      <p className="lead">
        Keep momentum in short daily sessions.
      </p>
      <button type="button" className="primary" onClick={onStartLearning}>
        Start Learning
      </button>
    </section>
  );
}
