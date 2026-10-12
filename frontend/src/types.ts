export type ExportFormat = "dialogue" | "timestamps";

export interface TranscriptSegment {
  id: string;
  speaker_id: string;
  start: number;
  end: number;
  text: string;
}

export interface TranscriptResult {
  duration_sec: number;
  language?: string | null;
  speakers: Record<string, string>;
  segments: TranscriptSegment[];
  diarization_engine?: string | null;
  diarization_note?: string | null;
}

export interface Job {
  id: string;
  status: string;
  stage: string;
  message: string;
  original_filename: string;
  error?: string | null;
  created_at?: string | null;
  result?: TranscriptResult | null;
}

export interface JobEvent {
  status: string;
  stage: string;
  message: string;
  error?: string | null;
}
