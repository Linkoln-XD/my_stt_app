import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  audioUrl,
  deleteJob,
  exportTxt,
  getJob,
  rediarizeJob,
  saveTranscript,
  subscribeJobEvents,
} from "../api";
import { AudioPlayerControls } from "../components/AudioPlayerControls";
import { ErrorNotice } from "../components/ErrorNotice";
import { ProcessingProgress } from "../components/ProcessingProgress";
import { ScrollJumpButtons } from "../components/ScrollJumpButtons";
import type { ExportFormat, Job, TranscriptSegment } from "../types";
import { parseJobError, type AppError } from "../utils/errors";

export function JobPage() {
  const { jobId } = useParams<{ jobId: string }>();
  const navigate = useNavigate();
  const [job, setJob] = useState<Job | null>(null);
  const [error, setError] = useState<AppError | null>(null);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [exportFormat, setExportFormat] = useState<ExportFormat>("dialogue");
  const [mergeAdjacent, setMergeAdjacent] = useState(true);
  const [saveState, setSaveState] = useState<"idle" | "saving" | "saved">("idle");
  const [rediarizing, setRediarizing] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const audioRef = useRef<HTMLAudioElement>(null);
  const saveTimer = useRef<number | null>(null);
  const listRef = useRef<HTMLUListElement>(null);

  const load = useCallback(async () => {
    if (!jobId) return;
    setJob(await getJob(jobId));
  }, [jobId]);

  useEffect(() => {
    if (!jobId) return;
    void load().catch((e) => setError(e as AppError));
  }, [jobId, load]);

  useEffect(() => {
    if (!jobId || !job || job.status === "done" || job.status === "failed") return;
    return subscribeJobEvents(
      jobId,
      (ev) => {
        setJob((prev) =>
          prev
            ? {
                ...prev,
                status: ev.status,
                stage: ev.stage,
                message: ev.message,
                error: ev.error,
              }
            : prev,
        );
        if (ev.status === "done") void load();
      },
      (err) => setError(err),
    );
  }, [jobId, job?.status, load]);

  const segments = job?.result?.segments ?? [];
  const speakers = job?.result?.speakers ?? {};

  const filteredSegments = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    if (!q) return segments;
    return segments.filter((s) => s.text.toLowerCase().includes(q));
  }, [segments, searchQuery]);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio || !segments.length) return;
    const onTime = () => {
      const t = audio.currentTime;
      const hit = segments.find((s) => t >= s.start && t < s.end);
      setActiveId(hit?.id ?? null);
    };
    audio.addEventListener("timeupdate", onTime);
    return () => audio.removeEventListener("timeupdate", onTime);
  }, [segments]);

  const speakerIds = useMemo(() => Object.keys(speakers), [speakers]);

  function updateSegmentText(id: string, text: string) {
    if (!job?.result) return;
    const next = job.result.segments.map((s) => (s.id === id ? { ...s, text } : s));
    patchLocal({ segments: next });
  }

  function updateSpeakerName(speakerId: string, name: string) {
    if (!job?.result) return;
    patchLocal({ speakers: { ...job.result.speakers, [speakerId]: name } });
  }

  function patchLocal(partial: {
    segments?: TranscriptSegment[];
    speakers?: Record<string, string>;
  }) {
    setJob((prev) => {
      if (!prev?.result) return prev;
      return {
        ...prev,
        result: {
          ...prev.result,
          segments: partial.segments ?? prev.result.segments,
          speakers: partial.speakers ?? prev.result.speakers,
        },
      };
    });
    scheduleSave(partial);
  }

  function scheduleSave(partial: {
    segments?: TranscriptSegment[];
    speakers?: Record<string, string>;
  }) {
    if (!jobId) return;
    setSaveState("saving");
    if (saveTimer.current) window.clearTimeout(saveTimer.current);
    saveTimer.current = window.setTimeout(() => {
      void saveTranscript(jobId, partial)
        .then(() => setSaveState("saved"))
        .catch((e) => setError(e as AppError))
        .finally(() => {
          window.setTimeout(() => setSaveState("idle"), 1500);
        });
    }, 600);
  }

  async function copyAll() {
    if (!jobId) return;
    const text = await exportTxt(jobId, exportFormat, mergeAdjacent);
    await navigator.clipboard.writeText(text);
  }

  async function downloadTxt() {
    if (!jobId || !job) return;
    const text = await exportTxt(jobId, exportFormat, mergeAdjacent);
    const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${job.original_filename.replace(/\.[^.]+$/, "")}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  }

  function seekTo(seg: TranscriptSegment) {
    const audio = audioRef.current;
    if (!audio) return;
    audio.currentTime = seg.start;
    void audio.play();
    setActiveId(seg.id);
  }

  function goHome() {
    if (jobId) void deleteJob(jobId).catch(() => undefined);
    navigate("/");
  }

  if (!jobId) return null;

  if (!job) {
    return <p className="muted">Загрузка…</p>;
  }

  const processing = job.status !== "done" && job.status !== "failed";
  const jobError = job.status === "failed" ? parseJobError(job.error) : null;

  return (
    <div className="stack gap-lg job-page">
      <div className="job-head">
        <button type="button" className="back-link btn-link" onClick={goHome}>
          ← Новый файл
        </button>
        <h1 className="job-title">{job.original_filename}</h1>
      </div>

      {processing && (
        <ProcessingProgress stage={job.stage} message={job.message} active={processing} />
      )}

      {jobError && <ErrorNotice error={jobError} />}
      {error && <ErrorNotice error={error} onDismiss={() => setError(null)} />}

      {job.status === "done" && job.result && (
        <>
          {job.result.diarization_note && (
            <div className="alert">{job.result.diarization_note}</div>
          )}

          <div className="toolbar card">
            <div className="toolbar-group">
              <span className="toolbar-label">Экспорт TXT</span>
              <select
                value={exportFormat}
                onChange={(e) => setExportFormat(e.target.value as ExportFormat)}
              >
                <option value="dialogue">Диалог (Спикер: текст)</option>
                <option value="timestamps">С таймкодами [00:01:23]</option>
              </select>
              <label className="checkbox">
                <input
                  type="checkbox"
                  checked={mergeAdjacent}
                  onChange={(e) => setMergeAdjacent(e.target.checked)}
                />
                Склеить соседние реплики одного спикера
              </label>
            </div>
            <div className="toolbar-actions">
              <button
                type="button"
                className="btn"
                disabled={rediarizing}
                onClick={() => {
                  if (!jobId) return;
                  setRediarizing(true);
                  void rediarizeJob(jobId)
                    .then(setJob)
                    .catch((e) => setError(e as AppError))
                    .finally(() => setRediarizing(false));
                }}
              >
                {rediarizing ? "Роли…" : "Пересчитать роли"}
              </button>
              <button type="button" className="btn" onClick={() => void copyAll().catch((e) => setError(e as AppError))}>
                Копировать
              </button>
              <button type="button" className="btn btn-primary" onClick={() => void downloadTxt().catch((e) => setError(e as AppError))}>
                Сохранить .txt
              </button>
              {saveState === "saving" && <span className="muted small">Сохранение…</span>}
              {saveState === "saved" && <span className="muted small">Сохранено</span>}
            </div>
          </div>

          {speakerIds.length > 0 && (
            <details className="card speaker-collapse">
              <summary className="speaker-collapse-summary">
                <span className="speaker-collapse-chevron" aria-hidden>
                  ▶
                </span>
                <span className="speaker-collapse-title">Имена спикеров</span>
                <span className="speaker-collapse-hint">нажмите, чтобы развернуть</span>
              </summary>
              <div className="speaker-grid">
                {speakerIds.map((sid) => (
                  <label key={sid} className="field">
                    <span className="field-label">{sid}</span>
                    <input
                      value={speakers[sid] ?? ""}
                      onChange={(e) => updateSpeakerName(sid, e.target.value)}
                    />
                  </label>
                ))}
              </div>
            </details>
          )}

          <div className="search-row card">
            <label className="field field-grow">
              <span className="field-label">Поиск по тексту</span>
              <input
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Слово или фраза…"
              />
            </label>
            {searchQuery && (
              <p className="muted small">
                Найдено блоков: {filteredSegments.length} из {segments.length}
              </p>
            )}
          </div>

          <div className="transcript-layout">
            <div className="card player-card">
              <AudioPlayerControls audioRef={audioRef} src={audioUrl(jobId)} />
              <p className="muted small">Клик по реплике — перемотка к фразе</p>
            </div>

            <div className="card transcript-card">
              <ul className="transcript-list" ref={listRef}>
                {filteredSegments.map((seg) => (
                  <li
                    key={seg.id}
                    id={`seg-${seg.id}`}
                    className={`transcript-item ${activeId === seg.id ? "segment-active" : ""} ${searchQuery && seg.text.toLowerCase().includes(searchQuery.trim().toLowerCase()) ? "search-hit" : ""}`}
                  >
                    <button type="button" className="transcript-meta" onClick={() => seekTo(seg)}>
                      <span className="speaker-tag">{speakers[seg.speaker_id] ?? seg.speaker_id}</span>
                      <span className="time-tag">{formatHms(seg.start)}</span>
                    </button>
                    <textarea
                      className="segment-text"
                      rows={2}
                      value={seg.text}
                      onChange={(e) => updateSegmentText(seg.id, e.target.value)}
                    />
                  </li>
                ))}
              </ul>
              {searchQuery && filteredSegments.length === 0 && (
                <p className="muted">Ничего не найдено</p>
              )}
            </div>
          </div>
          <ScrollJumpButtons />
        </>
      )}
    </div>
  );
}

function formatHms(sec: number): string {
  const s = Math.floor(sec);
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const r = s % 60;
  if (h > 0) return `${h}:${m.toString().padStart(2, "0")}:${r.toString().padStart(2, "0")}`;
  return `${m}:${r.toString().padStart(2, "0")}`;
}
