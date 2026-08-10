import { useState } from "react";
import { useRouter } from "next/router";
import api from "../lib/api";

export default function LoginPage() {
  const [isSignUp, setIsSignUp] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      if (isSignUp) {
        // Register new account
        await api.post("/auth/signup", { email, password });
      }

      // Log in to retrieve JWT token
      const form = new URLSearchParams();
      form.append("username", email);
      form.append("password", password);

      const { data } = await api.post("/auth/login", form, {
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
      });

      localStorage.setItem("token", data.access_token);
      router.push("/listings");
    } catch (err) {
      if (isSignUp) {
        setError(err.response?.data?.detail || "Registration failed. Email may already be taken.");
      } else {
        setError("Incorrect email or password.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-brand-50">
      <form onSubmit={handleSubmit} className="bg-white rounded-xl shadow-sm p-8 w-full max-w-sm">
        <h1 className="text-xl font-medium text-brand-800 mb-6">
          {isSignUp ? "Create a Repricer Account" : "Sign in to Repricer"}
        </h1>

        <label className="text-sm text-gray-600">Email</label>
        <input
          type="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full mt-1 mb-4 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-brand-400"
        />

        <label className="text-sm text-gray-600">Password</label>
        <input
          type="password"
          required
          minLength={8}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full mt-1 mb-6 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-brand-400"
        />

        {error && <p className="text-sm text-red-600 mb-4">{error}</p>}

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-brand-600 text-white py-2 rounded-md hover:bg-brand-800 transition disabled:opacity-50"
        >
          {loading ? "Processing..." : isSignUp ? "Create Account" : "Sign in"}
        </button>

        <div className="mt-4 text-center">
          <button
            type="button"
            onClick={() => {
              setIsSignUp(!isSignUp);
              setError("");
            }}
            className="text-xs text-brand-600 hover:underline"
          >
            {isSignUp ? "Already have an account? Sign in" : "Don't have an account? Sign up"}
          </button>
        </div>
      </form>
    </div>
  );
}
