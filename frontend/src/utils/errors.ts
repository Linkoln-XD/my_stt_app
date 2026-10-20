export type ErrorType =
  | "unknown"
  | "network"
  | "admin_invalid_credentials"
  | "admin_unauthorized"
  | "missing_filename"
  | "file_too_large"
  | "invalid_audio"
  | "audio_too_long"
  | "invalid_settings"
  | "processing_failed"
  | "job_not_found";

export interface AppError {
  type: ErrorType;
  message: string;
}

const ERROR_LABELS: Record<string, string> = {
  network: "Сеть",
  admin_invalid_credentials: "Доступ администратора",
  admin_unauthorized: "Доступ администратора",
  missing_filename: "Файл",
  file_too_large: "Размер файла",
  invalid_audio: "Аудио",
  audio_too_long: "Длительность",
  invalid_settings: "Настройки",
  processing_failed: "Обработка",
  job_not_found: "Задача",
  unknown: "Ошибка",
};

export function errorTypeLabel(type: ErrorType): string {
  return ERROR_LABELS[type] ?? ERROR_LABELS.unknown;
}

export async function parseApiError(res: Response): Promise<AppError> {
  let body: unknown = null;
  try {
    body = await res.json();
  } catch {
    return { type: "unknown", message: res.statusText || "Неизвестная ошибка" };
  }
  const detail = (body as { detail?: unknown })?.detail;
  if (typeof detail === "string") {
    return { type: "unknown", message: detail };
  }
  if (detail && typeof detail === "object") {
    const d = detail as { type?: string; message?: string };
    return {
      type: (d.type as ErrorType) || "unknown",
      message: d.message || "Ошибка запроса",
    };
  }
  return { type: "unknown", message: "Ошибка запроса" };
}

export function parseJobError(raw: string | null | undefined): AppError {
  if (!raw) return { type: "processing_failed", message: "Ошибка обработки" };
  const match = /^\[([a-z_]+)\]\s*(.*)$/i.exec(raw);
  if (match) {
    return { type: (match[1] as ErrorType) || "processing_failed", message: match[2] || raw };
  }
  return { type: "processing_failed", message: raw };
}
