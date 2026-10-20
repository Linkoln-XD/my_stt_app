# Конфигурация

Файл: **`backend/.env`** (скопируйте из `backend/.env.example`).

Переменные читаются через Pydantic Settings; рабочая директория uvicorn — `backend/`.

## Переменные

| Переменная | По умолчанию | Описание |
|------------|--------------|----------|
| `ADMIN_USERNAME` | `admin` | Логин админ-панели |
| `ADMIN_PASSWORD` | `admin` | Пароль админ-панели (**смените**) |
| `HF_TOKEN` / `HUGGING_FACE_HUB_TOKEN` | — | Токен Hugging Face для pyannote |
| `DIARIZATION_BACKEND` | `auto` | `auto` \| `pyannote` \| `resemblyzer` |
| `DIARIZATION_DEVICE` | `cpu` | Устройство pyannote (`cpu` рекомендуется на Mac) |
| `WHISPER_MODEL` | `medium` | `medium`, `large-v3`, … |
| `WHISPER_DEVICE` | `cpu` | `cpu` на Mac |
| `WHISPER_COMPUTE_TYPE` | `int8` | `int8`, `float16`, … |
| `FFMPEG_PATH` | — | Явный путь к ffmpeg |
| `FFPROBE_PATH` | — | Явный путь к ffprobe |

## Режимы диаризации

| `DIARIZATION_BACKEND` | Поведение |
|------------------------|-----------|
| `auto` | pyannote при наличии `HF_TOKEN`, иначе Resemblyzer; при сбое pyannote — Resemblyzer |
| `pyannote` | Только pyannote (нужен токен и кэш моделей) |
| `resemblyzer` | Только локальная кластеризация по сегментам ASR |

## Производительность (ориентир, Mac CPU)

| Модель Whisper | ~20–30 мин аудио |
|----------------|------------------|
| `medium` + int8 | десятки минут обработки |
| `large-v3` | дольше, точнее ASR |

Диаризация Resemblyzer добавляет минуты в зависимости от числа сегментов; pyannote — отдельный тяжёлый этап.

## Данные на диске

| Путь | Содержимое |
|------|------------|
| `data/uploads/` | Исходные загрузки |
| `data/processed/` | WAV 16 kHz, промежуточные файлы |
| `data/jobs.db` | SQLite |
| `~/.cache/huggingface/` | Веса Whisper / pyannote |

Каталог `data/` в `.gitignore`.

## Системные настройки (runtime)

Файл `data/system_settings.json` — меняется через админ-панель:

- `model_tier`: `light` | `medium` | `heavy`
- `max_duration_minutes`: одно из 5, 10, 15, 30, 45, 60

При первом запуске создаётся автоматически.
