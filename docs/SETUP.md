# Установка и первый запуск

Приложение рассчитано на **macOS**, локальный запуск (один пользователь, без авторизации).

## 1. Зависимости системы

Рекомендуется [Homebrew](https://brew.sh):

```bash
brew install python@3.12 ffmpeg node
```

| Компонент | Зачем |
|-----------|--------|
| **Python 3.11+** | Backend (системный 3.9 на macOS не подходит) |
| **ffmpeg** | Конвертация аудио (если нет в PATH — используется `imageio-ffmpeg` из pip) |
| **Node.js 20+** | Frontend (Vite + React) |

## 2. Backend

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
cp .env.example .env
```

Отредактируйте `backend/.env` при необходимости (см. [CONFIGURATION.md](./CONFIGURATION.md)).

### Модели

**Whisper** скачивается при первой транскрипции.

**Роли (спикеры):**

- **Без `HF_TOKEN`** — используется **Resemblyzer** (локально, офлайн после установки pip-зависимостей).
- **С `HF_TOKEN`** — в режиме `auto` сначала **pyannote** (обычно точнее), при ошибке — Resemblyzer.

Для pyannote один раз (нужен интернет):

1. Примите лицензии: [speaker-diarization-3.1](https://huggingface.co/pyannote/speaker-diarization-3.1), [segmentation-3.0](https://huggingface.co/pyannote/segmentation-3.0).
2. Создайте токен на [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens).
3. Укажите `HF_TOKEN` в `.env`.
4. Выполните:

```bash
python scripts/download_models.py
```

После кэширования весов pyannote можно работать **офлайн**.

## 3. Frontend

```bash
cd frontend
npm install
```

## 4. Запуск

Два терминала из корня репозитория:

```bash
./scripts/run_backend.sh    # http://127.0.0.1:8000
./scripts/run_frontend.sh   # http://127.0.0.1:5173
```

Откройте **http://127.0.0.1:5173**.

Остановка:

```bash
./scripts/stop.sh
```

## 5. CLI (без веб-интерфейса)

```bash
cd backend && source .venv/bin/activate
python scripts/transcribe_cli.py /path/to/audio.mp3 \
  -o result.json \
  --txt transcript.txt \
  --format dialogue
```

Форматы TXT: `dialogue`, `timestamps`.
