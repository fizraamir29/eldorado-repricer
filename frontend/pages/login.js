import { useState } from "react";
import { useRouter } from "next/router";
import api from "../lib/api";

export default function LoginPage() {
  const [isSignUp, setIsSignUp] = useState(false);
  const [fullName, setFullName] = useState("");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [age, setAge] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      if (isSignUp) {
        // Try registering new account
        try {
          await api.post("/auth/signup", {
            email,
            password,
            full_name: fullName || null,
            username: username || null,
            age: age ? parseInt(age, 10) : null,
          });
        } catch (signupErr) {
          // If already registered, attempt auto-login with provided credentials
          const detail = signupErr.response?.data?.detail || "";
          if (!detail.includes("already registered") && !detail.includes("already taken")) {
            throw signupErr;
          }
        }
      }

      // Log in to retrieve JWT access token
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
        setError(err.response?.data?.detail || "Registration/Login failed. Please check your inputs or try signing in.");
      } else {
        setError(err.response?.data?.detail || "Incorrect email/username or password.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-emerald-50/60 p-4">
      <form onSubmit={handleSubmit} className="bg-white rounded-2xl shadow-lg border border-emerald-100 p-8 w-full max-w-md transition-all duration-200">
        <div className="text-center mb-6">
          <div className="w-12 h-12 bg-emerald-600 rounded-xl flex items-center justify-center text-white font-bold text-xl mx-auto mb-3 shadow-md shadow-emerald-200">
            R
          </div>
          <h1 className="text-2xl font-bold text-slate-800">
            {isSignUp ? "Create Admin Account" : "Sign in to Repricer"}
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Automated Eldorado Repricing & Inventory Portal
          </p>
        </div>

        {isSignUp && (
          <>
            <div className="mb-4">
              <label className="block text-xs font-semibold text-slate-600 uppercase tracking-wider mb-1">
                Full Name
              </label>
              <input
                type="text"
                required
                placeholder="John Doe"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="w-full px-3.5 py-2.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 text-slate-900 bg-white placeholder-slate-400 text-sm font-medium"
              />
            </div>

            <div className="grid grid-cols-2 gap-3 mb-4">
              <div>
                <label className="block text-xs font-semibold text-slate-600 uppercase tracking-wider mb-1">
                  Username
                </label>
                <input
                  type="text"
                  required
                  placeholder="admin_user"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="w-full px-3.5 py-2.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 text-slate-900 bg-white placeholder-slate-400 text-sm font-medium"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-600 uppercase tracking-wider mb-1">
                  Age
                </label>
                <input
                  type="number"
                  min="13"
                  max="120"
                  required
                  placeholder="25"
                  value={age}
                  onChange={(e) => setAge(e.target.value)}
                  className="w-full px-3.5 py-2.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 text-slate-900 bg-white placeholder-slate-400 text-sm font-medium"
                />
              </div>
            </div>
          </>
        )}

        <div className="mb-4">
          <label className="block text-xs font-semibold text-slate-600 uppercase tracking-wider mb-1">
            Email Address
          </label>
          <input
            type="email"
            required
            placeholder="admin@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full px-3.5 py-2.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 text-slate-900 bg-white placeholder-slate-400 text-sm font-medium"
          />
        </div>

        <div className="mb-6">
          <label className="block text-xs font-semibold text-slate-600 uppercase tracking-wider mb-1">
            Password
          </label>
          <input
            type="password"
            required
            minLength={8}
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full px-3.5 py-2.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 text-slate-900 bg-white placeholder-slate-400 text-sm font-medium"
          />
        </div>

        {error && (
          <div className="p-3 mb-4 text-xs font-medium text-red-700 bg-red-50 border border-red-200 rounded-lg">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-emerald-600 text-white font-semibold py-3 rounded-lg hover:bg-emerald-700 active:bg-emerald-800 transition-colors shadow-md shadow-emerald-200 disabled:opacity-50 text-sm cursor-pointer"
        >
          {loading ? "Processing..." : isSignUp ? "Create Account" : "Sign in"}
        </button>

        <div className="mt-6 text-center border-t border-slate-100 pt-4">
          <button
            type="button"
            onClick={() => {
              setIsSignUp(!isSignUp);
              setError("");
            }}
            className="text-xs font-medium text-emerald-600 hover:text-emerald-800 hover:underline"
          >
            {isSignUp ? "Already have an account? Sign in" : "Don't have an account? Sign up"}
          </button>
        </div>
      </form>
    </div>
  );
}
