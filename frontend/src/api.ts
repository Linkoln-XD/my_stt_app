import type { ExportFormat, Job } from "./types";

const base = "";

export async function listJobs(): Promise<Job[]> {
  const res = await fetch(`${base}/api/transcriptions`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getJob(id: string): Promise<Job> {
  const res = await fetch(`${base}/api/transcriptions/${id}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function uploadAudio(file: File): Promise<Job> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${base}/api/transcriptions`, { method: "POST", body: form });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? detail;
    } catch {
      /* ignore */
    }
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return res.json();
}

export function subscribeJobEvents(
  id: string,
  onEvent: (data: import("./types").JobEvent) => void,
): () => void {
  const es = new EventSource(`${base}/api/transcriptions/${id}/events`);
  es.onmessage = (ev) => {
    onEvent(JSON.parse(ev.data));
  };
  return () => es.close();
}

export async function saveTranscript(
  id: string,
  payload: { speakers?: Record<string, string>; segments?: import("./types").TranscriptSegment[] },
): Promise<Job> {
  const res = await fetch(`${base}/api/transcriptions/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function exportTxt(
  id: string,
  format: ExportFormat,
  mergeAdjacent: boolean,
): Promise<string> {
  const res = await fetch(`${base}/api/transcriptions/${id}/export.txt`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ format, merge_adjacent: mergeAdjacent }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.text();
}

export function audioUrl(id: string): string {
  return `${base}/api/transcriptions/${id}/audio`;
}

export async function rediarizeJob(id: string): Promise<Job> {
  const res = await fetch(`${base}/api/transcriptions/${id}/rediarize`, { method: "POST" });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function deleteJob(id: string): Promise<void> {
  const res = await fetch(`${base}/api/transcriptions/${id}`, { method: "DELETE" });
  if (!res.ok) throw new Error(await res.text());
}
