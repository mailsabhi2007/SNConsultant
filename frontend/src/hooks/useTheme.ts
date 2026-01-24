import { useEffect } from "react";
import { useUIStore } from "@/stores/uiStore";

export function useTheme() {
  const { theme, setTheme } = useUIStore();

  useEffect(() => {
    const root = document.documentElement;

    const applyTheme = (newTheme: "light" | "dark") => {
      root.classList.remove("light", "dark");
      root.classList.add(newTheme);
    };

    if (theme === "system") {
      const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");

      const handleChange = (e: MediaQueryListEvent | MediaQueryList) => {
        applyTheme(e.matches ? "dark" : "light");
      };

      handleChange(mediaQuery);
      mediaQuery.addEventListener("change", handleChange);

      return () => {
        mediaQuery.removeEventListener("change", handleChange);
      };
    } else {
      applyTheme(theme);
    }
  }, [theme]);

  return {
    theme,
    setTheme,
    isDark:
      theme === "dark" ||
      (theme === "system" &&
        window.matchMedia("(prefers-color-scheme: dark)").matches),
  };
}
