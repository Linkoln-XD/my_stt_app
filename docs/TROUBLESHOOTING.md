# Решение проблем

## Видео (AVI, MKV) не загружается или «нет аудиодорожки»

Приложение берёт **первую звуковую дорожку** из контейнера. Нужен рабочий ffmpeg/ffprobe (см. ниже).

Если в файле только видео без звука — будет явная ошибка при загрузке.

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

## «Потеряно соединение с сервером прогресса» в конце обработки

Если расшифровка **уже готова**, это ложное срабатывание закрытия SSE (исправлено во frontend). Обновите страницу или перезапустите Vite. Реальная ошибка сети — если job завис в `processing`.

## `metadata_errors` / `processing_failed` при расшифровке

**Причина:** несовместимая версия **PyAV** (`av` 16+) с `faster-whisper`.

**Решение:** в `requirements-docker.txt` зафиксировано `av>=12,<16`. Пересоберите образ:

```bash
docker compose up --build -d
```

## `403 Forbidden` / `model_download_failed` при смене модели в админке

**Причина:** для выбранного tier (лёгкая=`small`, средняя=`medium`, тяжёлая=`large-v3`) весов ещё нет в локальном кэше Hugging Face, а скачивание с `huggingface.co` блокируется сетью или HTTP-прокси (в т.ч. sandbox Cursor). Модель `medium` могла уже быть в кэше — поэтому раньше всё работало.

**Решение:** один раз скачать все Whisper-модели без блокирующего прокси:

```bash
cd backend && source .venv/bin/activate
python scripts/download_models.py --whisper-only
```

Либо запустите backend в обычном терминале (не через sandbox с `HTTP_PROXY`) и повторите расшифровку — веса подтянутся при первом job.

Кэш: `~/.cache/huggingface/hub/models--Systran--faster-whisper-*`. Для Docker скопируйте кэш: `./scripts/bundle_whisper_cache.sh`.

## Job долго в processing / «В очереди»

**Первый файл после установки:** этап **«Загрузка модели»** — скачивание Whisper с Hugging Face (несколько GB). В Docker это может занять **5–15+ минут** при медленном интернете. Смотрите текст под прогресс-баром и `docker compose logs -f`.

**Несколько загрузок подряд:** одновременно обрабатывается **один** файл; остальные ждут (**«Ожидание слота»**).

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
