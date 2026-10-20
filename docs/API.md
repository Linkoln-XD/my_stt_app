# HTTP API

Base URL при локальном запуске: **http://127.0.0.1:8000**

Frontend проксирует `/api` через Vite (`frontend/vite.config.ts`).

## Health

`GET /api/health` → `{ "ok": true }`

## Публичные настройки

`GET /api/settings/public`

```json
{
  "model_tier": "medium",
  "max_duration_minutes": 30,
  "allowed_duration_minutes": [5, 10, 15, 30, 45, 60],
  "model_tiers": ["light", "medium", "heavy"]
}
```

## Админ

См. [ADMIN.md](./ADMIN.md): `POST /api/admin/login`, `GET/PATCH /api/admin/settings` с заголовком `X-Admin-Token`.

## Jobs

### Создать (загрузка)

`POST /api/transcriptions`

- Content-Type: `multipart/form-data`
- Поле: `file` — аудио или видео с аудиодорожкой (mp3, wav, m4a, ogg, **avi**, **mkv**, mp4, mov, …)
- Лимиты: **30 минут**, ~500 MB

Ответ `201`: объект job (`status`: `pending` → `processing` → `done` | `failed`).

Ошибки (пример):

```json
{
  "detail": {
    "type": "audio_too_long",
    "message": "Длительность 35.0 мин превышает лимит 30 мин",
    "extra": { "duration_sec": 2100, "max_duration_sec": 1800 }
  }
}
```

Типы: `missing_filename`, `file_too_large`, `invalid_audio`, `audio_too_long`, `processing_failed`, …

### Получить job

`GET /api/transcriptions/{job_id}`

В `result` — расшифровка после `status: done`.

### Прогресс (SSE)

`GET /api/transcriptions/{job_id}/events`

Server-Sent Events, JSON в `data:`:

```json
{ "status": "processing", "stage": "asr", "message": "…", "error": null }
```

### Обновить текст / имена спикеров

`PATCH /api/transcriptions/{job_id}`

```json
{
  "speakers": { "SPEAKER_00": "Клиент" },
  "segments": [ … ]
}
```

Можно передать только изменённые поля.

### Пересчитать роли

`POST /api/transcriptions/{job_id}/rediarize`

Повторная диаризация по сохранённому WAV **без** повторного ASR. Текст сегментов сохраняется.

### Аудио для плеера

`GET /api/transcriptions/{job_id}/audio`

### Экспорт TXT

`POST /api/transcriptions/{job_id}/export.txt`

```json
{
  "format": "dialogue",
  "merge_adjacent": true
}
```

`format`: `dialogue` | `timestamps`

Ответ: `text/plain; charset=utf-8`

### Удалить job

`DELETE /api/transcriptions/{job_id}` → `204`

Удаляет запись и файлы upload/processed для job.
