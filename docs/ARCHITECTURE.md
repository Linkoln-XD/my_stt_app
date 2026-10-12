# Архитектура

## Обзор

```text
Browser (React)
    │  REST + SSE
    ▼
FastAPI (backend/app)
    │  SQLite jobs
    │  data/uploads, data/processed
    ▼
Worker (thread pool, один job за раз)
    │
    ├─ ffmpeg / imageio-ffmpeg  → mono 16 kHz WAV
    ├─ faster-whisper           → текст + таймкоды сегментов
    └─ diarization              → speaker_id на сегмент
           ├─ pyannote (если HF_TOKEN, backend=auto|pyannote)
           └─ Resemblyzer + sklearn (fallback / resemblyzer)
```

## Структура репозитория

```text
my_stt_app/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI, CORS
│   │   ├── config.py            # .env, пути data/
│   │   ├── db.py                # SQLite JobRow
│   │   ├── worker.py            # фоновая обработка
│   │   ├── routers/             # HTTP API
│   │   ├── models/schemas.py    # Pydantic
│   │   └── services/
│   │       ├── audio.py         # ffprobe/ffmpeg
│   │       ├── transcription.py # пайплайн ASR + merge
│   │       ├── diarization.py   # pyannote + Resemblyzer
│   │       └── export.py        # TXT
│   ├── scripts/
│   │   ├── download_models.py
│   │   └── transcribe_cli.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/                    # React + Vite + TypeScript
├── scripts/                     # run_*.sh, stop.sh
├── docs/                        # документация
└── data/                        # runtime (gitignore)
```

## Пайплайн транскрипции

1. **Upload** — файл сохраняется в `data/uploads/{job_id}/`, проверка длительности (≤ 30 мин).
2. **Prepare** — WAV 16 kHz mono в `data/processed/{job_id}/`.
3. **ASR** — faster-whisper, `language=None` (auto RU/EN), VAD.
4. **Diarization** — назначение `speaker_id` каждому ASR-сегменту.
5. **Result** — JSON в SQLite + отдача в UI.

Прогресс: SSE `GET /api/transcriptions/{id}/events` (stage, message).

## Диаризация

### pyannote

Полноценная диаризация по аудио, затем сопоставление ASR-сегментов с интервалами спикеров (overlap, midpoint, nearest turn).

### Resemblyzer

Эмбеддинг на каждый достаточно длинный ASR-сегмент (≥ ~0.35 с), кластеризация (Agglomerative + silhouette) → число спикеров 1…8.

## Данные job

Результат (`TranscriptResult`):

- `segments[]` — id, speaker_id, start, end, text
- `speakers` — отображаемые имена (редактируются в UI)
- `diarization_engine` — `pyannote` | `resemblyzer` | `none`
- `diarization_note` — предупреждение для пользователя (опционально)

## Ограничения MVP

- Один активный worker (очередь без параллельной ML на нескольких файлах).
- Только localhost в CORS.
- История jobs в SQLite на той же машине.
