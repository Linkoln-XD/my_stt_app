import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { fetchPublicSettings, uploadAudio } from "../api";
import { ErrorNotice } from "../components/ErrorNotice";
import type { AppError } from "../utils/errors";

export function HomePage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<AppError | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [maxMin, setMaxMin] = useState(30);

  useEffect(() => {
    void fetchPublicSettings()
      .then((s) => setMaxMin(s.max_duration_minutes))
      .catch(() => {
        /* ignore */
      });
  }, []);

  async function handleFile(file: File) {
    setError(null);
    setLoading(true);
    try {
      const job = await uploadAudio(file);
      navigate(`/jobs/${job.id}`);
    } catch (e) {
      setError(e as AppError);
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
    <div className="home-upload-only">
      <section
        className={`dropzone dropzone-hero ${dragOver ? "dropzone-active" : ""}`}
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={onDrop}
      >
        <p className="dropzone-title">Перетащите файл сюда</p>
        <p className="muted">
          Аудио: MP3, WAV, M4A, OGG · видео: AVI, MKV, MP4, MOV · до {maxMin} мин
        </p>
        <label className="btn btn-primary" title="Выбрать аудио- или видеофайл для расшифровки">
          {loading ? "Загрузка…" : "Выбрать файл"}
          <input
            type="file"
            accept="audio/*,video/*,.avi,.mkv,.mp4,.mov,.webm"
            hidden
            disabled={loading}
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) void handleFile(file);
            }}
          />
        </label>
      </section>
      {error && <ErrorNotice error={error} onDismiss={() => setError(null)} />}
    </div>
  );
}
