import { useState } from "react";
import { Link, Route, Routes, useLocation } from "react-router-dom";
import { SettingsModals } from "./components/SettingsModals";
import { HomePage } from "./pages/HomePage";
import { JobPage } from "./pages/JobPage";

export default function App() {
  const [settingsOpen, setSettingsOpen] = useState(false);
  const location = useLocation();
  const isHome = location.pathname === "/";

  return (
    <div className="app-shell">
      <header className="app-header">
        <Link to="/" className="brand">
          STT
        </Link>
        <span className="brand-sub">расшифровка с ролями · локально</span>
        {isHome && (
          <button
            type="button"
            className="btn header-settings"
            onClick={() => setSettingsOpen(true)}
            aria-label="Настройки"
            title="Настройки"
          >
            <svg
              className="settings-icon"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.75"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 0 0 2.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 0 0 1.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 0 0-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 0 0-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 0 0-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 0 0-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 0 0 1.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065Z"
              />
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
            </svg>
          </button>
        )}
      </header>
      <main className="app-main">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/jobs/:jobId" element={<JobPage />} />
        </Routes>
      </main>
      <SettingsModals open={settingsOpen} onClose={() => setSettingsOpen(false)} />
    </div>
  );
}
