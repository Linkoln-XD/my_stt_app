import { useEffect, useState } from "react";
import { readStoredTheme, resolveInitialTheme, toggleTheme, type Theme } from "../utils/theme";

export function ThemeToggle() {
  const [theme, setTheme] = useState<Theme>(() => readStoredTheme() ?? resolveInitialTheme());

  useEffect(() => {
    setTheme(readStoredTheme() ?? resolveInitialTheme());
  }, []);

  const isDark = theme === "dark";
  const label = isDark ? "Переключить на светлую тему" : "Переключить на тёмную тему";

  return (
    <button
      type="button"
      className="btn header-icon-btn"
      onClick={() => setTheme((t) => toggleTheme(t))}
      aria-label={label}
      title={label}
    >
      {isDark ? (
        <svg className="header-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" aria-hidden="true">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M12 3v1.5M12 19.5V21M4.22 4.22l1.06 1.06M18.72 18.72l1.06 1.06M3 12h1.5M19.5 12H21M4.22 19.78l1.06-1.06M18.72 5.28l1.06-1.06M12 7.5a4.5 4.5 0 1 0 0 9 4.5 4.5 0 0 0 0-9Z"
          />
        </svg>
      ) : (
        <svg className="header-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" aria-hidden="true">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M21 12.79A9 9 0 1 1 11.21 3a7 7 0 0 0 9.79 9.79Z"
          />
        </svg>
      )}
    </button>
  );
}
