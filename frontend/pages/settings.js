import { useState, useEffect } from "react";
import { Sun, Moon, Palette, Sliders, Bell, Save, CheckCircle2, ShieldCheck, Zap, Sparkles, UserCheck, Clock, Mail, User } from "lucide-react";
import Layout from "../components/Layout";
import { useTheme, ACCENTS } from "../lib/useTheme";
import api from "../lib/api";

export default function SettingsPage() {
  const { mode, toggleMode, accent, changeAccent, accentObj } = useTheme();
  const [userProfile, setUserProfile] = useState(null);

  const [botDefaults, setBotDefaults] = useState({
    undercut_step: "0.01",
    check_interval_minutes: "5",
    auto_greeting_enabled: true,
    auto_greeting_message: "Hello! Thanks for purchasing from our Eldorado store. Your order is being processed automatically.",
  });

  const [notifications, setNotifications] = useState({
    sound_alerts: true,
    price_change_bell: true,
    error_alerts: true,
  });

  const [savedSuccess, setSavedSuccess] = useState(false);

  useEffect(() => {
    api.get("/auth/me")
      .then((res) => setUserProfile(res.data))
      .catch(() => {});
  }, []);

  function handleSave() {
    localStorage.setItem("bot_defaults", JSON.stringify(botDefaults));
    localStorage.setItem("notification_prefs", JSON.stringify(notifications));
    setSavedSuccess(true);
    setTimeout(() => setSavedSuccess(false), 3000);
  }

  return (
    <Layout>
      <div className="max-w-4xl mx-auto space-y-8">
        {/* Page Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-5">
          <div>
            <h2 className="text-2xl font-bold text-white font-heading tracking-tight flex items-center gap-2">
              <Sliders className={accentObj.text} size={24} /> Dashboard Customization & Settings
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              Customize your theme, accent color palette, bot default parameters, and view active admin account metadata.
            </p>
          </div>

          <button
            onClick={handleSave}
            className={`flex items-center gap-2 bg-gradient-to-r ${accentObj.primary} text-white font-semibold text-sm px-5 py-2.5 rounded-xl ${accentObj.shadow} transition-all`}
          >
            {savedSuccess ? <CheckCircle2 size={18} /> : <Save size={18} />}
            {savedSuccess ? "Settings Saved!" : "Save All Settings"}
          </button>
        </div>

        {/* Section 0: Admin Account Information */}
        {userProfile && (
          <div className="bg-[#131B2A] border border-slate-800 rounded-2xl p-6 shadow-glass space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className={`w-10 h-10 rounded-xl bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 flex items-center justify-center`}>
                  <UserCheck size={20} />
                </div>
                <div>
                  <h3 className="text-base font-semibold text-white font-heading">Active Administrator Profile</h3>
                  <p className="text-xs text-slate-400">Registered seller account metadata stored in backend database</p>
                </div>
              </div>
              <span className="text-xs px-3 py-1 rounded-full font-medium border bg-emerald-500/10 text-emerald-400 border-emerald-500/30 flex items-center gap-1.5">
                <ShieldCheck size={12} /> Admin Authenticated
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 pt-2">
              <div className="bg-[#0F172A] border border-slate-800/80 rounded-xl p-3.5">
                <div className="text-[11px] text-slate-400 uppercase tracking-wider mb-1 flex items-center gap-1">
                  <User size={12} /> Full Name
                </div>
                <div className="text-sm font-semibold text-white truncate">{userProfile.full_name || "N/A"}</div>
              </div>

              <div className="bg-[#0F172A] border border-slate-800/80 rounded-xl p-3.5">
                <div className="text-[11px] text-slate-400 uppercase tracking-wider mb-1 flex items-center gap-1">
                  <User size={12} /> Username
                </div>
                <div className="text-sm font-semibold text-emerald-400 truncate">@{userProfile.username || "admin"}</div>
              </div>

              <div className="bg-[#0F172A] border border-slate-800/80 rounded-xl p-3.5">
                <div className="text-[11px] text-slate-400 uppercase tracking-wider mb-1 flex items-center gap-1">
                  <Mail size={12} /> Email Address
                </div>
                <div className="text-sm font-semibold text-white truncate">{userProfile.email}</div>
              </div>

              <div className="bg-[#0F172A] border border-slate-800/80 rounded-xl p-3.5">
                <div className="text-[11px] text-slate-400 uppercase tracking-wider mb-1 flex items-center gap-1">
                  <Clock size={12} /> Last Login Time
                </div>
                <div className="text-xs font-semibold text-slate-300 truncate">
                  {userProfile.last_login_at ? new Date(userProfile.last_login_at).toLocaleString() : "First Login"}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Section 0.5: Chrome Extension Setup */}
        <div className="bg-[#131B2A] border border-emerald-500/30 rounded-2xl p-6 shadow-glass space-y-4">
          <div className="flex items-center gap-3">
            <div className={`w-10 h-10 rounded-xl bg-amber-500/20 text-amber-400 border border-amber-500/30 flex items-center justify-center`}>
              <Zap size={20} />
            </div>
            <div>
              <h3 className="text-base font-semibold text-white font-heading">Chrome Extension Token</h3>
              <p className="text-xs text-slate-400">Use this token to connect your local Chrome Extension to this Dashboard</p>
            </div>
          </div>
          
          <div className="bg-[#0F172A] border border-slate-800 rounded-xl p-4 flex items-center justify-between">
            <div className="text-sm font-mono text-slate-300 truncate mr-4">
              {typeof window !== 'undefined' ? localStorage.getItem("token") || "No token found" : ""}
            </div>
            <button
              onClick={() => {
                if (typeof window !== 'undefined') {
                  const token = localStorage.getItem("token");
                  if (token) {
                    navigator.clipboard.writeText(token);
                    alert("Token copied to clipboard!");
                  }
                }
              }}
              className="whitespace-nowrap px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold rounded-lg transition-colors border border-slate-700"
            >
              Copy Token
            </button>
          </div>
        </div>

        {/* Section 1: Appearance & Theme Customization */}
        <div className="bg-[#131B2A] border border-slate-800 rounded-2xl p-6 shadow-glass space-y-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className={`w-10 h-10 rounded-xl ${accentObj.bg} ${accentObj.border} border flex items-center justify-center ${accentObj.text}`}>
                <Palette size={20} />
              </div>
              <div>
                <h3 className="text-base font-semibold text-white font-heading">Appearance & Color Theme</h3>
                <p className="text-xs text-slate-400">Choose between Light/Dark mode and primary accent color</p>
              </div>
            </div>
            <span className={`text-xs px-3 py-1 rounded-full font-medium border ${accentObj.bg} ${accentObj.text} ${accentObj.border}`}>
              Active: {accentObj.name}
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
            {/* Mode Switcher */}
            <div className="bg-[#0F172A] border border-slate-800 rounded-xl p-4">
              <label className="text-xs font-semibold text-slate-300 block mb-3 uppercase tracking-wider">
                Display Mode
              </label>
              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={() => mode !== "dark" && toggleMode()}
                  className={`flex-1 flex items-center justify-center gap-2 py-3 rounded-xl text-sm font-medium border transition ${
                    mode === "dark"
                      ? `${accentObj.bg} ${accentObj.text} ${accentObj.border} font-bold`
                      : "bg-slate-800/40 text-slate-400 border-slate-700 hover:text-white"
                  }`}
                >
                  <Moon size={16} /> Dark Mode
                </button>

                <button
                  type="button"
                  onClick={() => mode !== "light" && toggleMode()}
                  className={`flex-1 flex items-center justify-center gap-2 py-3 rounded-xl text-sm font-medium border transition ${
                    mode === "light"
                      ? `${accentObj.bg} ${accentObj.text} ${accentObj.border} font-bold`
                      : "bg-slate-800/40 text-slate-400 border-slate-700 hover:text-white"
                  }`}
                >
                  <Sun size={16} /> Light Mode
                </button>
              </div>
            </div>

            {/* Accent Color Selector */}
            <div className="bg-[#0F172A] border border-slate-800 rounded-xl p-4">
              <label className="text-xs font-semibold text-slate-300 block mb-3 uppercase tracking-wider">
                Accent Color Palette
              </label>
              <div className="grid grid-cols-3 gap-2">
                {Object.entries(ACCENTS).map(([key, item]) => (
                  <button
                    key={key}
                    type="button"
                    onClick={() => changeAccent(key)}
                    className={`flex flex-col items-center gap-1.5 p-2.5 rounded-xl border text-xs font-medium transition ${
                      accent === key
                        ? "border-amber-400 bg-amber-500/10 text-white font-bold"
                        : "border-slate-800 bg-slate-900/60 text-slate-400 hover:text-white"
                    }`}
                  >
                    <span className="w-5 h-5 rounded-full shadow" style={{ backgroundColor: item.hex }}></span>
                    {item.name.split(" ")[0]}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Section 2: Bot Default Repricing Rules */}
        <div className="bg-[#131B2A] border border-slate-800 rounded-2xl p-6 shadow-glass space-y-5">
          <div className="flex items-center gap-3">
            <div className={`w-10 h-10 rounded-xl ${accentObj.bg} ${accentObj.border} border flex items-center justify-center ${accentObj.text}`}>
              <Zap size={20} />
            </div>
            <div>
              <h3 className="text-base font-semibold text-white font-heading">Default Repricing Parameters</h3>
              <p className="text-xs text-slate-400">Configure default undercut step and automated check frequency</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-slate-400 block mb-1.5 font-medium">Default Undercut Step ($)</label>
              <input
                type="number"
                step="0.01"
                value={botDefaults.undercut_step}
                onChange={(e) => setBotDefaults({ ...botDefaults, undercut_step: e.target.value })}
                className="w-full px-3.5 py-2.5 bg-[#0F172A] border border-slate-700 rounded-xl text-sm text-white focus:outline-none focus:border-amber-500"
              />
              <span className="text-[11px] text-slate-500 mt-1 block">Default: $0.01 (repositions 1 cent below lowest competitor)</span>
            </div>

            <div>
              <label className="text-xs text-slate-400 block mb-1.5 font-medium">Default Scan Interval (minutes)</label>
              <input
                type="number"
                value={botDefaults.check_interval_minutes}
                onChange={(e) => setBotDefaults({ ...botDefaults, check_interval_minutes: e.target.value })}
                className="w-full px-3.5 py-2.5 bg-[#0F172A] border border-slate-700 rounded-xl text-sm text-white focus:outline-none focus:border-amber-500"
              />
              <span className="text-[11px] text-slate-500 mt-1 block">Default: 5 minutes continuous checking</span>
            </div>
          </div>

          <div className="pt-2">
            <label className="text-xs text-slate-400 block mb-1.5 font-medium">Auto-Greeting Buyer Responder Template</label>
            <textarea
              rows={3}
              value={botDefaults.auto_greeting_message}
              onChange={(e) => setBotDefaults({ ...botDefaults, auto_greeting_message: e.target.value })}
              className="w-full px-3.5 py-2.5 bg-[#0F172A] border border-slate-700 rounded-xl text-sm text-white focus:outline-none focus:border-amber-500"
            />
          </div>
        </div>

        {/* Section 3: Notification Preferences */}
        <div className="bg-[#131B2A] border border-slate-800 rounded-2xl p-6 shadow-glass space-y-5">
          <div className="flex items-center gap-3">
            <div className={`w-10 h-10 rounded-xl ${accentObj.bg} ${accentObj.border} border flex items-center justify-center ${accentObj.text}`}>
              <Bell size={20} />
            </div>
            <div>
              <h3 className="text-base font-semibold text-white font-heading">Notification & Alert Preferences</h3>
              <p className="text-xs text-slate-400">Control live alerts and notification updates</p>
            </div>
          </div>

          <div className="space-y-3">
            <label className="flex items-center justify-between p-3.5 bg-[#0F172A] border border-slate-800 rounded-xl cursor-pointer">
              <div>
                <div className="text-sm font-medium text-white">Live Price Change Bell Notifications</div>
                <div className="text-xs text-slate-400">Show live popups and bell badge when listing price is updated</div>
              </div>
              <input
                type="checkbox"
                checked={notifications.price_change_bell}
                onChange={(e) => setNotifications({ ...notifications, price_change_bell: e.target.checked })}
                className="w-5 h-5 accent-amber-500 rounded"
              />
            </label>

            <label className="flex items-center justify-between p-3.5 bg-[#0F172A] border border-slate-800 rounded-xl cursor-pointer">
              <div>
                <div className="text-sm font-medium text-white">API Connection Error Alerts</div>
                <div className="text-xs text-slate-400">Alert immediately if Eldorado API endpoint returns rate limits or credentials issue</div>
              </div>
              <input
                type="checkbox"
                checked={notifications.error_alerts}
                onChange={(e) => setNotifications({ ...notifications, error_alerts: e.target.checked })}
                className="w-5 h-5 accent-amber-500 rounded"
              />
            </label>
          </div>
        </div>
      </div>
    </Layout>
  );
}
