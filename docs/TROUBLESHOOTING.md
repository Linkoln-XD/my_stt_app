# Решение проблем

## Internal Server Error при загрузке файла

**Причина:** не найден `ffprobe` / `ffmpeg`.

**Решение:**

```bash
brew install ffmpeg
```

Либо переустановите backend-зависимости (`imageio-ffmpeg` в `requirements.txt` подставляет ffmpeg автоматически).

## Только «Спикер 1» на диалоге

1. Откройте job — строка **«Движок ролей»**. Если `none` или note про pyannote — роли не считались.
2. Нажмите **«Пересчитать роли»** после обновления backend.
3. Без `HF_TOKEN` используется **resemblyzer** — для похожих голосов или одного доминирующего спикера может остаться один кластер.
4. Для лучшего качества: `HF_TOKEN`, `download_models.py`, `DIARIZATION_BACKEND=auto`.

## Job долго в processing

Нормально для CPU: ASR на 20–30 мин аудио может занимать **десятки минут**. Смотрите этап в UI (SSE).

Параллельно обрабатывается **один** файл.

## pyannote: ошибка доступа к модели

- Примите лицензии на Hugging Face (см. [SETUP.md](./SETUP.md)).
- Проверьте `HF_TOKEN` в `backend/.env`.
- Запустите `python scripts/download_models.py` из каталога `backend`.

## Backend не видит .env

Файл должен быть **`backend/.env`**, не в корне репозитория. Перезапустите uvicorn после изменений.

## Порт занят

```bash
./scripts/stop.sh
```

Затем снова `run_backend.sh` / `run_frontend.sh`.

## npm / node не найден

```bash
brew install node
```

Либо portable Node в `.tools/node` (не в git) — см. комментарий в [README.md](../README.md).
