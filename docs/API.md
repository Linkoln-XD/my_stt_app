# HTTP API

Base URL при локальном запуске: **http://127.0.0.1:8000**

Frontend проксирует `/api` через Vite (`frontend/vite.config.ts`).

## Health

`GET /api/health` → `{ "ok": true }`

## Jobs

### Список

`GET /api/transcriptions`

Последние jobs (до 50), новые первыми.

### Создать (загрузка)

`POST /api/transcriptions`

- Content-Type: `multipart/form-data`
- Поле: `file` — аудио (mp3, wav, m4a, ogg, …)
- Лимиты: **30 минут**, ~500 MB

Ответ `201`: объект job (`status`: `pending` → `processing` → `done` | `failed`).

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
