import type { ExportFormat, Job } from "./types";
import { parseApiError, type AppError } from "./utils/errors";

const base = "";

export type ModelTier = "light" | "medium" | "heavy";

export interface PublicSettings {
  model_tier: ModelTier;
  max_duration_minutes: number;
  allowed_duration_minutes: number[];
  model_tiers: ModelTier[];
}

export interface SystemSettings {
  model_tier: ModelTier;
  max_duration_minutes: number;
}

async function ensureOk(res: Response): Promise<Response> {
  if (!res.ok) throw await parseApiError(res);
  return res;
}

export async function fetchPublicSettings(): Promise<PublicSettings> {
  const res = await ensureOk(await fetch(`${base}/api/settings/public`));
  return res.json();
}

export async function adminLogin(username: string, password: string): Promise<{ token: string }> {
  const res = await fetch(`${base}/api/admin/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  await ensureOk(res);
  return res.json();
}

export async function fetchAdminSettings(token: string): Promise<SystemSettings> {
  const res = await ensureOk(
    await fetch(`${base}/api/admin/settings`, {
      headers: { "X-Admin-Token": token },
    }),
  );
  return res.json();
}

export async function updateAdminSettings(
  token: string,
  payload: Partial<SystemSettings>,
): Promise<SystemSettings> {
  const res = await ensureOk(
    await fetch(`${base}/api/admin/settings`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json", "X-Admin-Token": token },
      body: JSON.stringify(payload),
    }),
  );
  return res.json();
}

export async function getJob(id: string): Promise<Job> {
  const res = await ensureOk(await fetch(`${base}/api/transcriptions/${id}`));
  return res.json();
}

export async function uploadAudio(file: File): Promise<Job> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${base}/api/transcriptions`, { method: "POST", body: form });
  await ensureOk(res);
  return res.json();
}

export function subscribeJobEvents(
  id: string,
  onEvent: (data: import("./types").JobEvent) => void,
  onError?: (err: AppError) => void,
): () => void {
  const es = new EventSource(`${base}/api/transcriptions/${id}/events`);
  let finished = false;

  es.onmessage = (ev) => {
    const data = JSON.parse(ev.data) as import("./types").JobEvent;
    onEvent(data);
    if (data.status === "done" || data.status === "failed") {
      finished = true;
      es.close();
    }
  };

  es.onerror = () => {
    // Browser fires onerror when the server closes SSE after done — not a real failure.
    if (finished || es.readyState === EventSource.CLOSED) {
      return;
    }
    onError?.({ type: "network", message: "Потеряно соединение с сервером прогресса" });
  };

  return () => {
    finished = true;
    es.close();
  };
}

export async function saveTranscript(
  id: string,
  payload: { speakers?: Record<string, string>; segments?: import("./types").TranscriptSegment[] },
): Promise<Job> {
  const res = await ensureOk(
    await fetch(`${base}/api/transcriptions/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
  );
  return res.json();
}

export async function exportTxt(
  id: string,
  format: ExportFormat,
  mergeAdjacent: boolean,
): Promise<string> {
  const res = await ensureOk(
    await fetch(`${base}/api/transcriptions/${id}/export.txt`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ format, merge_adjacent: mergeAdjacent }),
    }),
  );
  return res.text();
}

export function audioUrl(id: string): string {
  return `${base}/api/transcriptions/${id}/audio`;
}

export async function rediarizeJob(id: string): Promise<Job> {
  const res = await ensureOk(await fetch(`${base}/api/transcriptions/${id}/rediarize`, { method: "POST" }));
  return res.json();
}

export async function deleteJob(id: string): Promise<void> {
  await ensureOk(await fetch(`${base}/api/transcriptions/${id}`, { method: "DELETE" }));
}
