import { Link, Route, Routes } from "react-router-dom";
import { HomePage } from "./pages/HomePage";
import { JobPage } from "./pages/JobPage";

export default function App() {
  return (
    <div className="app-shell">
      <header className="app-header">
        <Link to="/" className="brand">
          STT
        </Link>
        <span className="brand-sub">расшифровка с ролями · локально</span>
      </header>
      <main className="app-main">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/jobs/:jobId" element={<JobPage />} />
        </Routes>
      </main>
    </div>
  );
}
