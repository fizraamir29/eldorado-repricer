import { createContext, useContext, useEffect, useState } from "react";

const ThemeContext = createContext();

export const ACCENTS = {
  yellow: {
    name: "Yellow / Gold",
    primary: "from-amber-500 to-yellow-400",
    text: "text-amber-400",
    bg: "bg-amber-500/10",
    border: "border-amber-500/30",
    badgeBg: "bg-amber-500/20",
    shadow: "shadow-glow-amber",
    hex: "#F59E0B",
  },
  emerald: {
    name: "Emerald Green",
    primary: "from-emerald-600 to-teal-500",
    text: "text-emerald-400",
    bg: "bg-emerald-500/10",
    border: "border-emerald-500/30",
    badgeBg: "bg-emerald-500/20",
    shadow: "shadow-glow-emerald",
    hex: "#10B981",
  },
  cyan: {
    name: "Electric Cyan",
    primary: "from-cyan-600 to-blue-500",
    text: "text-cyan-400",
    bg: "bg-cyan-500/10",
    border: "border-cyan-500/30",
    badgeBg: "bg-cyan-500/20",
    shadow: "shadow-glow-cyan",
    hex: "#06B6D4",
  },
};

export function ThemeProvider({ children }) {
  const [mode, setMode] = useState("dark");
  const [accent, setAccent] = useState("yellow"); // Default to Yellow as requested!

  useEffect(() => {
    const savedMode = localStorage.getItem("theme_mode");
    const savedAccent = localStorage.getItem("theme_accent");
    if (savedMode) setMode(savedMode);
    if (savedAccent && ACCENTS[savedAccent]) setAccent(savedAccent);
  }, []);

  function toggleMode() {
    const next = mode === "dark" ? "light" : "dark";
    setMode(next);
    localStorage.setItem("theme_mode", next);
  }

  function changeAccent(newAccent) {
    if (ACCENTS[newAccent]) {
      setAccent(newAccent);
      localStorage.setItem("theme_accent", newAccent);
    }
  }

  const accentObj = ACCENTS[accent] || ACCENTS.yellow;

  return (
    <ThemeContext.Provider value={{ mode, toggleMode, accent, changeAccent, accentObj }}>
      <div className={mode === "light" ? "light-mode" : "dark-mode"}>{children}</div>
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  return useContext(ThemeContext);
}
