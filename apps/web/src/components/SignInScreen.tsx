import { FormEvent } from "react";

type SignInScreenProps = {
  email: string;
  password: string;
  error: string;
  isSigningIn: boolean;
  onEmailChange: (value: string) => void;
  onPasswordChange: (value: string) => void;
  onSignIn: (event: FormEvent<HTMLFormElement>) => Promise<void>;
  onBack: () => void;
};

export default function SignInScreen({
  email,
  password,
  error,
  isSigningIn,
  onEmailChange,
  onPasswordChange,
  onSignIn,
  onBack
}: SignInScreenProps) {
  return (
    <section className="panel auth">
      <h2>Sign in to continue</h2>
      <p>After sign in, you will land directly on your last DSA problem.</p>

      <form onSubmit={onSignIn} className="authForm">
        <label htmlFor="email">Email</label>
        <input
          id="email"
          type="email"
          value={email}
          onChange={(event) => onEmailChange(event.target.value)}
          placeholder="you@example.com"
        />

        <label htmlFor="password">Password</label>
        <input
          id="password"
          type="password"
          value={password}
          onChange={(event) => onPasswordChange(event.target.value)}
          placeholder="Enter password"
        />

        {error && <p className="errorText">{error}</p>}

        <button type="submit" className="primary">
          {isSigningIn ? "Signing in..." : "Sign In"}
        </button>
        <button type="button" className="ghost" onClick={onBack}>
          Back
        </button>
      </form>
    </section>
  );
}
