import { useEffect, useSyncExternalStore } from "react";

type Theme = "dark" | "light";
let current: Theme = "dark";
const subs = new Set<() => void>();

function apply(t: Theme) {
  current = t;
  document.documentElement.classList.toggle("dark", t === "dark");
  localStorage.setItem("ss-theme", t);
  subs.forEach((s) => s());
}

export function initTheme() {
  const saved = localStorage.getItem("ss-theme");
  apply(saved === "light" ? "light" : "dark");
}

export function useTheme() {
  const theme = useSyncExternalStore(
    (l) => {
      subs.add(l);
      return () => subs.delete(l);
    },
    () => current,
    () => "dark" as Theme,
  );
  return { theme, setTheme: apply, toggle: () => apply(current === "dark" ? "light" : "dark") };
}

export function useInitTheme() {
  useEffect(() => initTheme(), []);
}
