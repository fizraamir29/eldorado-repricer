import { useState } from "react";
import { Link2, CheckCircle2, ShieldCheck, Lock, KeyRound, Info } from "lucide-react";
import Layout from "../components/Layout";
import api from "../lib/api";

export default function ConnectPage() {
  const [clientId, setClientId] = useState("");
  const [clientSecret, setClientSecret] = useState("");
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    try {
      await api.post("/auth/marketplace-credentials", {
        client_id: clientId.trim(),
        client_secret: clientSecret.trim(),
      });
      setSaved(true);
      setClientSecret("");
    } catch {
      setError("Couldn't save credentials. Make sure both Client ID and Client Secret are provided.");
    }
  }

  return (
    <Layout>
      <div className="max-w-2xl">
        <div className="bg-[#131B2A] rounded-2xl shadow-glass p-8 border border-slate-800">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 shadow-glow-emerald">
              <Link2 size={20} />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white font-heading">Connect Official Eldorado Seller API</h2>
              <div className="flex items-center gap-1.5 text-xs text-emerald-400 font-medium mt-0.5">
                <ShieldCheck size={14} /> Fernet AES-256 Application Layer Encryption & OAuth2 Auto-Refresh Enabled
              </div>
            </div>
          </div>

          <div className="text-xs text-slate-300 mt-4 mb-6 leading-relaxed bg-[#0F172A] p-4 rounded-xl border border-slate-800 space-y-2">
            <p>
              Your <strong className="text-white">Client Secret</strong> is encrypted in memory with Fernet AES-256 before storage.
              It is <strong className="text-white">never logged</strong>, <strong className="text-white">never returned in API responses</strong>, and <strong className="text-white">never exposed to the browser</strong>.
            </p>
            <div className="flex items-center gap-1.5 text-amber-400 font-medium pt-1">
              <Info size={14} /> Uses official Eldorado OAuth token authorization (<code className="text-amber-300 bg-amber-950/60 px-1 py-0.5 rounded">POST /api/authentication/seller/token</code>)
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-xs text-slate-400 font-semibold uppercase tracking-wider block mb-2">
                Client ID (Public Identifier)
              </label>
              <div className="relative">
                <input
                  type="text"
                  required
                  value={clientId}
                  onChange={(e) => setClientId(e.target.value)}
                  placeholder="e.g. a1b2c3d4-5678-90ab-cdef-1234567890ab"
                  className="w-full px-4 py-3 bg-[#0F172A] border border-slate-700 rounded-xl text-sm text-white focus:outline-none focus:border-emerald-500 transition font-mono"
                />
                <KeyRound size={16} className="absolute right-4 top-3.5 text-slate-500" />
              </div>
            </div>

            <div>
              <label className="text-xs text-slate-400 font-semibold uppercase tracking-wider block mb-2">
                Client Secret (Shown only at creation)
              </label>
              <div className="relative">
                <input
                  type="password"
                  required
                  value={clientSecret}
                  onChange={(e) => setClientSecret(e.target.value)}
                  placeholder="Paste your secret from Eldorado Client Credentials creation..."
                  className="w-full px-4 py-3 bg-[#0F172A] border border-slate-700 rounded-xl text-sm text-white focus:outline-none focus:border-emerald-500 transition font-mono"
                />
                <Lock size={16} className="absolute right-4 top-3.5 text-slate-500" />
              </div>
            </div>

            {error && <p className="text-sm text-rose-400 mt-2">{error}</p>}

            {saved && (
              <div className="text-sm text-emerald-400 mt-2 flex items-center gap-2 bg-emerald-500/10 p-3 rounded-xl border border-emerald-500/20 font-medium">
                <CheckCircle2 size={18} /> Eldorado Client Credentials encrypted and saved securely!
              </div>
            )}

            <button
              type="submit"
              className="w-full bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-semibold text-sm px-6 py-3 rounded-xl shadow-glow-emerald transition-all mt-4"
            >
              Save Credentials Securely
            </button>
          </form>
        </div>

        <div className="bg-[#131B2A]/60 border border-slate-800 rounded-xl p-4 mt-4 text-xs text-slate-400 space-y-2">
          <p className="font-semibold text-slate-300">How to generate your Eldorado Seller API credentials:</p>
          <ol className="list-decimal list-inside space-y-1 text-slate-400">
            <li>Log in to your Eldorado account (requires 50 total sales or unlocked Seller API access).</li>
            <li>Send a <code className="text-emerald-400 bg-slate-900 px-1 py-0.5 rounded">POST /api/client-credentials</code> request from your browser session to create a credential pair.</li>
            <li>Copy the returned <code className="text-emerald-400 bg-slate-900 px-1 py-0.5 rounded">clientId</code> and <code className="text-emerald-400 bg-slate-900 px-1 py-0.5 rounded">clientSecret</code> into the fields above.</li>
          </ol>
        </div>
      </div>
    </Layout>
  );
}
