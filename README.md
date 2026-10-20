# STT App — локальная расшифровка с ролями

**Развёртывание на сервере (Docker, порт, админ):** [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)

Веб-приложение для **macOS**: загрузка аудио/видео (до лимита, задаётся админом), распознавание **RU/EN**, разделение по спикерам, редактирование, плеер, экспорт TXT.

Одноразовый сценарий: **загрузил → получил расшифровку → ушёл** (без истории на главной).

## Быстрый старт

```bash
brew install python@3.12 ffmpeg node

cd backend && python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && cp .env.example .env

cd ../frontend && npm install

./scripts/run_backend.sh    # :8000
./scripts/run_frontend.sh   # :5173
```

→ **http://127.0.0.1:5173** · остановка: `./scripts/stop.sh`

## Docker (один контейнер)

Нужны [Docker](https://docs.docker.com/get-docker/) и Docker Compose v2.

**Развёртывание на сервере (пошагово, порт, админ):** [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)

```bash
cp backend/.env.example backend/.env   # задайте ADMIN_PASSWORD
cp compose.env.example .env            # при необходимости STT_PORT
mkdir -p docker-bundled-models/huggingface
docker compose up --build -d
./scripts/verify_deploy.sh
```

Полная инструкция для сервера: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

→ **http://127.0.0.1:8080** (UI и API на одном порту)

Данные — том `stt-data`. Кэш Whisper — каталог `docker-bundled-models/huggingface` (см. `./scripts/bundle_whisper_cache.sh`). Остановка: `docker compose down`.

## Документация

| Документ | Содержание |
|----------|------------|
| [docs/USER_GUIDE.md](docs/USER_GUIDE.md) | Интерфейс, форматы, экспорт |
| [docs/ADMIN.md](docs/ADMIN.md) | Админ-панель, логин, системные настройки |
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | **Сервер:** Docker, порт, админ |
| [docs/SETUP.md](docs/SETUP.md) | Установка, модели, CLI |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Пайплайн, структура кода |
| [docs/API.md](docs/API.md) | REST, SSE, коды ошибок |
| [docs/CONFIGURATION.md](docs/CONFIGURATION.md) | `.env`, лимиты |
| [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) | Типичные проблемы |
| [docs/CHANGELOG.md](docs/CHANGELOG.md) | История версий |

## Админ (кратко)

- Кнопка **⚙** на главной → логин (`ADMIN_USERNAME` / `ADMIN_PASSWORD` в `.env`, по умолчанию `admin` / `admin`).
- **Модель** в UI формальная; **лимит минут** — реальный для всех загрузок.

## Структура

```text
backend/   FastAPI, Whisper, diarization
frontend/  React + Vite
docs/      полная документация
scripts/   run_*.sh, stop.sh, run_docker.sh
Dockerfile docker-compose.yml
data/      runtime (gitignore)
```

## Лицензия

[MIT](LICENSE)
