import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { listJobs, uploadAudio } from "../api";
import type { Job } from "../types";

export function HomePage() {
  const navigate = useNavigate();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);

  const refresh = useCallback(async () => {
    try {
      setJobs(await listJobs());
    } catch {
      /* backend may be down on first load */
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  async function handleFile(file: File) {
    setError(null);
    setLoading(true);
    try {
      const job = await uploadAudio(file);
      navigate(`/jobs/${job.id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  function onDrop(ev: React.DragEvent) {
    ev.preventDefault();
    setDragOver(false);
    const file = ev.dataTransfer.files[0];
    if (file) void handleFile(file);
  }

  return (
    <div className="stack gap-lg">
      <section
        className={`dropzone ${dragOver ? "dropzone-active" : ""}`}
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={onDrop}
      >
        <p className="dropzone-title">Перетащите аудиофайл сюда</p>
        <p className="muted">MP3, WAV, M4A, OGG · до 30 минут</p>
        <label className="btn btn-primary">
          {loading ? "Загрузка…" : "Выбрать файл"}
          <input
            type="file"
            accept="audio/*"
            hidden
            disabled={loading}
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) void handleFile(file);
            }}
          />
        </label>
      </section>

      {error && <div className="alert alert-error">{error}</div>}

      {jobs.length > 0 && (
        <section className="card">
          <h2 className="section-title">Недавние</h2>
          <ul className="job-list">
            {jobs.map((j) => (
              <li key={j.id}>
                <Link to={`/jobs/${j.id}`} className="job-link">
                  <span className="job-name">{j.original_filename}</span>
                  <span className={`badge badge-${j.status}`}>{j.status}</span>
                </Link>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
