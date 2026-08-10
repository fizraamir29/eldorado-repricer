import Link from "next/link";
import { useRouter } from "next/router";
import { LayoutGrid, History, LogOut, Radio, Link2, BarChart3, ShieldCheck, Zap, Settings, Sun, Moon } from "lucide-react";
import NotificationBell from "./NotificationBell";
import useRealtime from "../lib/useRealtime";
import { useTheme } from "../lib/useTheme";

const NAV_ITEMS = [
  { href: "/listings", label: "Listings & Bot", icon: LayoutGrid },
  { href: "/analytics", label: "Market Analytics", icon: BarChart3 },
  { href: "/history", label: "Audit History", icon: History },
  { href: "/connect", label: "Connect API", icon: Link2 },
  { href: "/settings", label: "Settings", icon: Settings },
];

const PAGE_TITLES = {
  "/listings": "Listings & Repricing Bot Controls",
  "/analytics": "Marketplace Price Analytics & Infographics",
  "/history": "Price Change Audit History",
  "/connect": "Marketplace API Credentials",
  "/settings": "Dashboard Settings & Theme Customization",
};

export default function Layout({ children }) {
  const router = useRouter();
  const { connected, lastEvent } = useRealtime();
  const { mode, toggleMode, accentObj } = useTheme();

  function logout() {
    localStorage.removeItem("token");
    router.push("/login");
  }

  return (
    <div className={`min-h-screen flex text-slate-100 font-sans ${mode === "light" ? "bg-[#F8FAFC]" : "bg-[#0B0F17]"}`}>
      {/* Sidebar */}
      <aside className="w-64 bg-[#0F172A]/90 border-r border-slate-800/80 flex flex-col p-5 backdrop-blur-xl shrink-0">
        <div className="flex items-center gap-3 mb-8 px-2">
          <div className={`w-10 h-10 rounded-xl bg-gradient-to-tr ${accentObj.primary} flex items-center justify-center ${accentObj.shadow}`}>
            <Zap size={22} className="text-white fill-white" />
          </div>
          <div>
            <div className="text-lg font-bold tracking-tight text-white font-heading">Repricer Pro</div>
            <div className={`text-[11px] font-medium ${accentObj.text} flex items-center gap-1`}>
              <ShieldCheck size={12} /> Official API Automation
            </div>
          </div>
        </div>

        <nav className="flex flex-col gap-1.5 flex-1">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const active = router.pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all ${
                  active
                    ? `bg-gradient-to-r ${accentObj.primary} text-white ${accentObj.shadow}`
                    : "text-slate-400 hover:text-slate-100 hover:bg-slate-800/60"
                }`}
              >
                <Icon size={18} className={active ? "text-white" : "text-slate-400"} />
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="pt-4 border-t border-slate-800/80 space-y-2">
          <button
            onClick={logout}
            className="w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-medium text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 transition-all"
          >
            <LogOut size={18} />
            Log out
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-16 flex items-center justify-between px-8 border-b border-slate-800/80 bg-[#0F172A]/50 backdrop-blur-md sticky top-0 z-30">
          <div className="flex items-center gap-4">
            <h1 className="text-base font-semibold text-white tracking-wide">{PAGE_TITLES[router.pathname] || ""}</h1>
            <span
              className={`flex items-center gap-1.5 text-xs px-3 py-1 rounded-full font-medium border ${
                connected
                  ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                  : "bg-amber-500/10 text-amber-400 border-amber-500/30"
              }`}
            >
              <Radio size={12} className={connected ? "animate-pulse text-emerald-400" : ""} />
              {connected ? "WebSocket Connected" : "Reconnecting…"}
            </span>
          </div>

          <div className="flex items-center gap-4">
            {/* Quick Dark/Light Mode Toggle Button */}
            <button
              onClick={toggleMode}
              title={`Switch to ${mode === "dark" ? "Light" : "Dark"} Mode`}
              className="p-2 rounded-xl bg-slate-800/60 border border-slate-700 text-slate-300 hover:text-amber-400 transition"
            >
              {mode === "dark" ? <Sun size={18} className="text-amber-400" /> : <Moon size={18} className="text-indigo-400" />}
            </button>

            <NotificationBell liveEvent={lastEvent} />
          </div>
        </header>

        <main className="flex-1 p-8 overflow-y-auto">{children}</main>
      </div>
    </div>
  );
}
