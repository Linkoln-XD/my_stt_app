# STT App — локальная расшифровка с ролями

Веб-приложение для **macOS**: загрузка аудио (до **30 минут**), распознавание речи **RU/EN**, автоматическое разделение по спикерам, редактирование текста, плеер с подсветкой фразы, экспорт **TXT** (диалог или с таймкодами).

Работает **локально** (один пользователь, без аккаунтов). Данные хранятся в каталоге `data/` на вашей машине.

## Быстрый старт

```bash
# Зависимости: brew install python@3.12 ffmpeg node

cd backend && python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && cp .env.example .env

cd ../frontend && npm install

# из корня репозитория — два терминала:
./scripts/run_backend.sh
./scripts/run_frontend.sh
```

Откройте **http://127.0.0.1:5173**. Остановка: `./scripts/stop.sh`.

Подробная установка, pyannote и офлайн-кэш моделей — **[docs/SETUP.md](docs/SETUP.md)**.

## Возможности

- Drag-and-drop / выбор файла (MP3, WAV, M4A, OGG, …)
- Прогресс обработки (распознавание → роли → готово)
- Переименование спикеров, правка текста (автосохранение)
- **Пересчитать роли** без повторного ASR
- Плеер: клик по реплике → перемотка, подсветка текущей фразы
- Экспорт TXT: формат «Спикер: текст» или `[00:01:23] Спикер: текст`

## Диаризация (роли)

| Режим | Нужен интернет / HF | Качество |
|-------|---------------------|----------|
| **Resemblyzer** (по умолчанию без токена) | Нет после `pip install` | Хорошо на чётких диалогах |
| **pyannote** (`HF_TOKEN`, см. SETUP) | Один раз для загрузки весов | Обычно лучше на сложных записях |

Настройка: `DIARIZATION_BACKEND=auto` в `backend/.env` — **[docs/CONFIGURATION.md](docs/CONFIGURATION.md)**.

## Документация

| Документ | Описание |
|----------|----------|
| [docs/SETUP.md](docs/SETUP.md) | Установка, модели, CLI |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Пайплайн и структура кода |
| [docs/API.md](docs/API.md) | REST и SSE |
| [docs/CONFIGURATION.md](docs/CONFIGURATION.md) | Переменные окружения |
| [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) | Частые ошибки |

## Структура проекта

```text
backend/     FastAPI, faster-whisper, diarization
frontend/    React + Vite + TypeScript
scripts/     run_backend.sh, run_frontend.sh, stop.sh
docs/        документация
data/        uploads, SQLite (не в git)
```

## CLI

```bash
cd backend && source .venv/bin/activate
python scripts/transcribe_cli.py audio.mp3 -o out.json --txt out.txt --format timestamps
```

## Лицензия

[MIT](LICENSE)
