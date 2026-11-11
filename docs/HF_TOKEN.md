# Как получить HF_TOKEN для STT App

Токен **Hugging Face** (`HF_TOKEN`) — опциональная настройка. Без него приложение работает на **Whisper** и **Resemblyzer** (роли спикеров). С токеном доступны **pyannote** (точнее спикеры) и **длинные файлы в GigaAM** (сегментация речи).

Подробнее, зачем токен и чем отличается от Resemblyzer: таблица в [GUIDE.md — админка и HF_TOKEN](GUIDE.md).

## Зачем токен в этом проекте

| Возможность | Без `HF_TOKEN` | С `HF_TOKEN` |
|-------------|----------------|--------------|
| Whisper, любая длина в лимите админки | Да | Да |
| GigaAM, короткий файл (≈ до 25 с) | Да | Да |
| GigaAM, длинный файл | Нет | Да (нужна модель [segmentation-3.0](https://huggingface.co/pyannote/segmentation-3.0)) |
| Роли: pyannote | Нет (идёт Resemblyzer) | Да, при `DIARIZATION_BACKEND=auto` |

Whisper **не требует** токена для скачивания весов (публичные модели Systran), но без токена лимиты Hugging Face ниже — для офлайн-кэша это обычно не критично.

## Шаг 1. Регистрация

1. Откройте [huggingface.co/join](https://huggingface.co/join) и создайте аккаунт (или войдите).
2. Подтвердите email, если сервис попросит.

## Шаг 2. Примите лицензии pyannote

Модели pyannote **gated**: без принятия условий скачивание по токену не пройдёт.

Войдите на Hugging Face и на **каждой** странице нажмите **Agree and access repository** (или аналог):

1. [pyannote/speaker-diarization-3.1](https://huggingface.co/pyannote/speaker-diarization-3.1) — разметка спикеров.
2. [pyannote/segmentation-3.0](https://huggingface.co/pyannote/segmentation-3.0) — сегментация речи (нужна для **длинного GigaAM** и части пайплайна диаризации).

Если кнопки согласия нет, вы уже приняли лицензию или аккаунт не залогинен.

## Шаг 3. Создайте токен доступа

1. [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
2. **Create new token** (или **New token**).
3. Имя — любое, например `stt-app-server`.
4. Тип: **Read** (достаточно для скачивания моделей; **не** давайте Write, если не нужен).
5. Скопируйте значение (`hf_…`). **Второй раз его не покажут** — сохраните в менеджер паролей.

Не публикуйте токен в git, чатах и скриншотах. Файл `backend/.env` в репозиторий не коммитьте.

## Шаг 4. Пропишите токен в приложении

В корне репозитория:

```bash
cp backend/.env.example backend/.env   # если файла ещё нет
```

В `backend/.env`:

```env
HF_TOKEN=hf_ваш_токен_здесь
```

Альтернативное имя переменной, которое тоже понимает приложение: `HUGGING_FACE_HUB_TOKEN`.

### Локальный запуск

После правки перезапустите backend:

```bash
./scripts/stop.sh
./scripts/run_backend.sh
```

### Docker (сервер)

Токен читается из `backend/.env`, который подключает `docker-compose.gpu.yml`. После изменения:

```bash
docker compose -f docker-compose.gpu.yml up -d --force-recreate
```

## Шаг 5. Скачайте модели pyannote (рекомендуется)

Пока есть интернет, прогрейте кэш — тогда расшифровка не упрётся в загрузку в момент задачи.

**Локально:**

```bash
cd backend && source .venv/bin/activate
python scripts/download_models.py
```

**В GPU-контейнере:**

```bash
docker compose -f docker-compose.gpu.yml exec stt python scripts/download_models.py
```

Кэш Hugging Face на сервере по умолчанию лежит в `docker-bundled-models/huggingface` на хосте (том в compose).

Для **GigaAM** веса отдельно: `python scripts/download_models.py --gigaam` (CDN, не Hugging Face) — см. [GUIDE.md](GUIDE.md).

## Проверка

1. В `backend/.env` строка `HF_TOKEN=hf_…` без кавычек и пробелов.
2. После перезапуска backend/контейнера загрузите русский файл **длиннее ~30 с** с движком **GigaAM** в админке — ошибки `gigaam_requires_token` быть не должно.
3. На результате в поле движка ролей при `DIARIZATION_BACKEND=auto` может быть `pyannote` (если удалось выделить ≥2 спикеров).

Логи при проблемах: локально — терминал `run_backend.sh`; Docker — `docker compose -f docker-compose.gpu.yml logs -f`.

## Частые ошибки

| Симптом | Что сделать |
|---------|-------------|
| 401 / 403 при pyannote | Принять лицензии на обеих страницах моделей, токен **Read**, пересоздать контейнер |
| Задача падает с `gigaam_requires_token` | Токен не задан или контейнер не перечитал `.env`; нужна лицензия **segmentation-3.0** |
| Токен в `.env`, но не работает в Docker | Файл именно `backend/.env`, команда `--force-recreate` |
| «Один спикер» на весь диалог | Не всегда из‑за токена; см. раздел про роли в [GUIDE.md](GUIDE.md) |

## Отзыв токена

На [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens) удалите или отзовите токен. В `backend/.env` очистите `HF_TOKEN` и перезапустите сервис — снова будет Resemblyzer и Whisper без pyannote/GigaAM-longform.
