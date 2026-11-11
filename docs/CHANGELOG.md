# Changelog

## 0.3.1

- **Fix:** GigaAM ставится с GitHub (PyPI `gigaam==0.1.0` не знает `v3_e2e_rnnt`). В Docker-образ добавлен `git` для сборки.

- Гайд [docs/VERIFY_DEPLOY.md](VERIFY_DEPLOY.md) — исправление каждого сообщения `verify_deploy.sh`.
- Отдельный гайд [docs/HF_TOKEN.md](HF_TOKEN.md); ссылки из README и GUIDE.
- Документация: GigaAM, HF_TOKEN vs Resemblyzer, кэш на GPU-сервере, onnxruntime для VAD.
- Второй движок ASR: **GigaAM v3** (`v3_e2e_rnnt`, русский, пунктуация). Выбор в админке: Whisper или GigaAM.
- GigaAM только для русской речи; иначе понятная ошибка с предложением Whisper.
- Длинные файлы в GigaAM требуют `HF_TOKEN` и кэш `pyannote/segmentation-3.0`.
- `python scripts/download_models.py --gigaam` — заранее скачать веса GigaAM.

## 0.3.0

- Серверный образ NVIDIA: `Dockerfile.gpu` и `docker-compose.gpu.yml` (CUDA 12.8, PyTorch cu128). Whisper и pyannote идут на GPU, когда админка выбирает видеокарту.
- На пустом томе при видимой CUDA устройство по умолчанию — GPU. Уже сохранённые настройки не перезаписываются.
- Контейнер GPU-образа не остаётся работать, если видеокарта ему не видна.
- `./scripts/verify_deploy.sh --gpu` проверяет пароль администратора, health и что внутри контейнера видна CUDA.
- У контейнеров задан лимит памяти. Порт можно публиковать только на localhost через `STT_BIND`.
- Документация собрана в `README.md` и `docs/GUIDE.md`.

## 0.2.2

- Админ-панель: выбор устройства CPU/GPU (GPU только если доступна; CUDA приоритетнее MPS). Влияет на Whisper и pyannote.

## 0.2.1

- Админ-панель: выбор модели реально переключает Whisper (`small` / `medium` / `large-v3`).

## 0.2.0

- Админ-панель: модель (формально), лимит длительности (реально).
- Прогресс-бар при обработке (ускорение в начале, замедление к концу).
- Плеер с нативными controls браузера (громкость/mute в UI плеера).
- Поиск по тексту расшифровки; collapsible «Имена спикеров».
- Кнопки скролла в начало/конец страницы результата.
- Главная без истории; удаление job при «Новый файл».
- Структурированные ошибки API (`type` + `message`).
- Поддержка видео AVI/MKV (извлечение аудио).
- Resemblyzer fallback для ролей без HF_TOKEN.

## 0.1.0

- Первый MVP: upload, ASR, diarization, React UI, экспорт TXT.
