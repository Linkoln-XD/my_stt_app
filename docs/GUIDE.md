# Руководство STT App

Один документ по приложению: запуск, деплой, интерфейс, настройки, устройство и решение проблем. Краткие команды также есть в [README](../README.md).

Токен Hugging Face: пошагово — [HF_TOKEN.md](HF_TOKEN.md). Сообщения `./scripts/verify_deploy.sh` и как их исправить — [VERIFY_DEPLOY.md](VERIFY_DEPLOY.md).

Версия приложения: **0.3.1**.

## Что это

Веб-приложение расшифровывает аудио и видео на русском и английском и раскладывает текст по спикерам. Сценарий одноразовый: загрузили файл, получили расшифровку, ушли. Список прошлых задач на главной не показывается.

Стек: React и Vite, FastAPI, **faster-whisper** или **GigaAM v3**, для ролей — **pyannote** или **Resemblyzer**. За один раз обрабатывается один файл, остальные ждут в очереди.

Движок ASR задаётся в админке. **Whisper** — несколько языков (авто), три размера модели. **GigaAM** — русский, пунктуация и нормализация (`v3_e2e_rnnt`).

## Локальный запуск на macOS

Нужны Python 3.12, ffmpeg и Node.js 20+. Удобно поставить их через Homebrew:

```bash
brew install python@3.12 ffmpeg node
```

Из корня репозитория, в двух терминалах:

```bash
cp backend/.env.example backend/.env
./scripts/run_backend.sh     # http://127.0.0.1:8000
./scripts/run_frontend.sh    # http://127.0.0.1:5173
```

Откройте **http://127.0.0.1:5173**. Остановка обоих процессов: `./scripts/stop.sh`.

`run_backend.sh` создаёт `backend/.venv` при первом запуске и ставит `backend/requirements.txt` и `requirements-gigaam.txt` (GigaAM нужен Python **3.10+**). Если в системе только Python 3.9, скрипт сам скачает portable **3.12** в `.tools/python312` (`./scripts/ensure_python312.sh`). Файл настроек — `backend/.env`. После правки `.env` backend нужно перезапустить.

На Mac пункт GPU в админке использует Apple MPS только для pyannote. Whisper и GigaAM на Metal не считаются и остаются на CPU (faster-whisper / PyTorch). Пока администратор сам не включит GPU, новый локальный запуск работает на CPU.

### Модели при локальном запуске

Whisper скачивается при первой расшифровке в `~/.cache/huggingface`. Для фильтра тишины (VAD) в Whisper используется **onnxruntime** из `requirements.txt` (на старых Python 3.9 может понадобиться `numpy<2`).

Чтобы скачать все три размера Whisper заранее:

```bash
cd backend && source .venv/bin/activate
python scripts/download_models.py --whisper-only
```

Веса **GigaAM** — в `~/.cache/gigaam` (CDN SberDevices), отдельно от Hugging Face. Пакет ставится **с GitHub** (не PyPI `0.1.0`): в `requirements.txt` указан коммит upstream с `v3_e2e_rnnt`.

```bash
cd backend && source .venv/bin/activate
python scripts/download_models.py --gigaam
```

Роли без токена Hugging Face считает Resemblyzer, он ставится вместе с зависимостями. Для pyannote и длинного GigaAM нужен **`HF_TOKEN`** — регистрация, лицензии и прогрев кэша: **[HF_TOKEN.md](HF_TOKEN.md)**.

После настройки токена выполните `python scripts/download_models.py` (Whisper по уровням админки + pyannote). Кэш GigaAM прогревается отдельно флагом `--gigaam`.

### Командная строка без сайта

```bash
cd backend && source .venv/bin/activate
python scripts/transcribe_cli.py /path/to/audio.mp3 \
  -o result.json \
  --txt transcript.txt \
  --format dialogue
```

Формат `--format`: `dialogue` или `timestamps`. Модель и устройство CLI берутся из `WHISPER_MODEL` и `WHISPER_DEVICE` в `.env`. Веб-интерфейс эти две переменные не использует: там решает админка.

## Деплой на сервер с NVIDIA

Это основной способ поставить приложение на сервер. Образ описан в `Dockerfile.gpu`, запуск — `docker-compose.gpu.yml`.

Контейнер видит видеокарту и ставит PyTorch со сборкой CUDA 12.8 (`cu128`). Внутри лежат cuBLAS и cuDNN 9, они нужны faster-whisper. При выборе GPU в админке Whisper считает на CUDA в float16, pyannote тоже на CUDA.

Образ рассчитан на Linux x86_64 и карты от Turing и новее: RTX 20/30/40, T4, A10, L4, A100, H100, Blackwell. Для GTX 10-й серии и V100 этот образ не подходит.

| Что нужно на сервере | Зачем |
|----------------------|--------|
| Docker Engine 24+ и Docker Compose v2 | Сборка и запуск |
| Драйвер NVIDIA, в `nvidia-smi` CUDA Version **12.8 или выше** | Видеокарта доступна контейнеру |
| [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html) | Docker умеет пробрасывать GPU |
| 16 ГБ RAM | Лимит контейнера — 16 ГБ |
| 8 ГБ видеопамяти для тяжёлой модели, 4 ГБ хватает для средней | Whisper large-v3 в float16 плюс pyannote |
| 25–40 ГБ диска | Образ, кэш моделей, загрузки |
| Интернет на первую сборку и на первую загрузку модели | Дальше можно работать из кэша |

Проверка, что Docker видит карту, до сборки приложения:

```bash
nvidia-smi
docker run --rm --gpus all nvidia/cuda:12.8.1-cudnn-runtime-ubuntu24.04 nvidia-smi
```

Вторая команда должна напечатать ту же видеокарту. Если `nvidia-smi` на хосте работает, а в контейнере нет, поставьте NVIDIA Container Toolkit по ссылке выше и перезапустите Docker.

### Установка

Из каталога с репозиторием:

```bash
cp backend/.env.example backend/.env
```

Откройте `backend/.env` и задайте пароль администратора. Оставьте логин или смените его тоже:

```env
ADMIN_USERNAME=admin
ADMIN_PASSWORD=длинный_пароль
```

Пароль `admin` для сервера не годится: `./scripts/verify_deploy.sh` завершится с ошибкой, пока он не заменён.

Порт и адрес публикации:

```bash
cp compose.env.example .env
```

По умолчанию сайт слушает порт **8080** на всех интерфейсах (`STT_BIND=0.0.0.0`). Внутри контейнера приложение всегда слушает 8080, наружу Docker публикует `STT_PORT`.

Каталог кэша моделей:

```bash
mkdir -p docker-bundled-models/huggingface
```

Сборка и запуск:

```bash
docker compose -f docker-compose.gpu.yml up --build -d
./scripts/verify_deploy.sh --gpu
```

Если проверка падает — см. [VERIFY_DEPLOY.md](VERIFY_DEPLOY.md) (таблица по каждому ✗ и ⚠).

Первая сборка часто занимает десятки минут. Сайт открывается по адресу `http://<IP-сервера>:8080/`.

Скрипт проверки смотрит Docker, пароль, контейнер, `GET /api/health` и что внутри контейнера `gpu_available` истинно, а `gpu_backend` равен `cuda`. Если контейнер поднялся без видеокарты, он сам останавливается: в логе будет текст про драйвер и toolkit.

На пустом томе устройство по умолчанию — GPU. Уже записанный `data/system_settings.json` скрипт и приложение не перезаписывают. Если проверка пишет, что CUDA видна, а устройство осталось CPU, откройте админку и включите GPU.

### Кэш Whisper

Без кэша модель `medium` (около 1.5 ГБ) скачается при первой расшифровке в каталог `docker-bundled-models/huggingface` на хосте. Этот каталог смонтирован в контейнер. Повторно качать её не нужно.

Чтобы перенести уже скачанный кэш с другой машины, на той машине выполните `./scripts/bundle_whisper_cache.sh` и скопируйте на сервер каталог `docker-bundled-models/huggingface`. Другой путь задаётся в корневом `.env`:

```env
STT_HF_CACHE_HOST=/srv/stt/huggingface
```

Три размера админки — это Whisper `small`, `medium` и `large-v3`. Если в кэше только `medium`, лёгкая и тяжёлая модели скачаются при первом выборе, когда есть доступ к huggingface.co.

### Кэш GigaAM на сервере

```bash
docker compose -f docker-compose.gpu.yml exec stt python scripts/download_models.py --gigaam
```

Нужен исходящий доступ к CDN GigaAM. В админке выберите движок **GigaAM** и при длинных русских записях задайте `HF_TOKEN` — [HF_TOKEN.md](HF_TOKEN.md).

### Управление

Команды из корня репозитория:

| Действие | Команда |
|----------|---------|
| Статус | `docker compose -f docker-compose.gpu.yml ps` |
| Логи | `docker compose -f docker-compose.gpu.yml logs -f` |
| Остановить | `docker compose -f docker-compose.gpu.yml down` |
| Запустить снова | `docker compose -f docker-compose.gpu.yml up -d` |
| Обновить код | `git pull && docker compose -f docker-compose.gpu.yml up --build -d` |
| Проверить | `./scripts/verify_deploy.sh --gpu` |

`docker compose down` не удаляет том `stt-data` (загрузки, база задач, системные настройки) и не удаляет кэш моделей на хосте.

После смены `backend/.env`:

```bash
docker compose -f docker-compose.gpu.yml up -d --force-recreate
```

Тот же проект не нужно одновременно запускать ещё и обычным `docker compose up`: оба файла описывают сервис `stt` и один том `stt-data`.

### HTTPS

Своей авторизации пользователей нет: кто открыл адрес, тот может загрузить файл в пределах лимита. Для доступа из интернета поставьте перед приложением Caddy или nginx с HTTPS и по желанию ограничьте источник по IP или VPN.

В корневом `.env` оставьте приложение только на локальном интерфейсе:

```env
STT_BIND=127.0.0.1
STT_PORT=8080
```

Пример Caddy:

```caddy
stt.example.com {
    reverse_proxy 127.0.0.1:8080
}
```

Браузер ходит на один адрес, интерфейс и API с него же, отдельно CORS настраивать не нужно. Порт 8080 в файрволе наружу можно не открывать. Откройте 443.

Смените `ADMIN_PASSWORD` до того, как отправите адрес другим людям.

## Локальный Docker без видеокарты

`Dockerfile` и `docker-compose.yml` собирают CPU-образ. Он нужен для проверки на Mac, где GPU в контейнер не попадает, и для машины без NVIDIA. На сервере с видеокартой ставьте GPU-образ из раздела выше: в CPU-образе PyTorch без CUDA, и админка не покажет видеокарту.

```bash
cp backend/.env.example backend/.env   # свой ADMIN_PASSWORD
cp compose.env.example .env
mkdir -p docker-bundled-models/huggingface
docker compose up --build -d
./scripts/verify_deploy.sh
```

Сайт: **http://127.0.0.1:8080/**. Лимит памяти этого контейнера — 8 ГБ. Остановка: `docker compose down`.

## Как пользоваться

1. Откройте сайт.
2. Перетащите файл или нажмите «Выбрать файл».
3. Дождитесь обработки. Под полосой прогресса написан текущий этап.
4. Послушайте запись, поправьте текст, при необходимости переименуйте спикеров.
5. Скопируйте текст или скачайте TXT.
6. «← Новый файл» возвращает на главную и удаляет эту задачу с сервера вместе с файлами.

Форматы: MP3, WAV, M4A, OGG и другое аудио; видео AVI, MKV, MP4, MOV, WebM. Из видео берётся первая аудиодорожка. Если звука нет, загрузка завершится ошибкой. Длительность ограничена настройкой администратора, по умолчанию 30 минут, допустимый диапазон ползунка — 10–120. Размер файла — до 500 МБ.

На странице результата:

| Элемент | Что делает |
|---------|------------|
| Плеер | Воспроизведение, перемотка, громкость и mute |
| Реплика | Клик по времени перематывает запись и подсвечивает фразу |
| Имена спикеров | Раскрывающийся блок, имена сохраняются на сервере |
| Поиск | Фильтр реплик без учёта регистра |
| ↑ / ↓ | Прокрутка в начало и в конец страницы |
| Пересчитать роли | Повторная диаризация по уже готовому WAV, текст не распознаётся заново |

Экспорт TXT:

- **Диалог** — `Спикер: текст`
- **С таймкодами** — `[00:01:23] Спикер: текст`
- Галочка склеивает соседние реплики одного спикера

В шапке переключается светлая и тёмная тема.

Первый файл после установки может долго висеть на этапе загрузки модели: качается Whisper. Расшифровка 20–30 минут аудио на CPU занимает десятки минут. На GPU то же аудио заметно быстрее, но точное время зависит от карты и выбранной модели.

## Админка

Кнопка **⚙** на главной. Логин и пароль — `ADMIN_USERNAME` и `ADMIN_PASSWORD` из `backend/.env`. После входа токен лежит в `sessionStorage` браузера до обновления страницы. На сервере сессия живёт 8 часов и пропадает при перезапуске процесса.

Настройки общие для всех загрузок и пишутся в `system_settings.json` внутри каталога данных:

| Параметр | Эффект |
|----------|--------|
| Движок: Whisper / GigaAM | Whisper — автоязык и уровни small/medium/large-v3. GigaAM — только русский, с пунктуацией (`v3_e2e_rnnt`) |
| Модель Whisper (только для Whisper) | `small` / `medium` / `large-v3`. Новые веса подгружаются на следующей задаче |
| Устройство: процессор / видеокарта | GPU доступно, когда процесс видит CUDA или Apple MPS. Нет устройства — пункт выключен, сохранённое `gpu` записывается как `cpu` |
| Максимальная длительность | 10–120 минут, проверяется при загрузке |

На CUDA Whisper, GigaAM и pyannote могут работать на видеокарте. На Apple MPS Whisper и GigaAM остаются на CPU, pyannote может использовать MPS.

Ориентир по видеопамяти при float16: Whisper `small` ~1 ГБ, `medium` ~2 ГБ, `large-v3` ~4–6 ГБ; GigaAM v3 e2e на GPU ~2–3 ГБ; плюс pyannote при токене. На **8 ГБ** (RTX 3070) не ставьте одновременно heavy Whisper и GigaAM без перезапуска — держите один движок в админке.

Кэш GigaAM: `python scripts/download_models.py --gigaam` (веса в `~/.cache/gigaam`). В Docker этот каталог по умолчанию **не** смонтирован на хост (в отличие от Hugging Face); после `docker compose up` прогрейте веса командой `exec … download_models.py --gigaam` или примите повторную загрузку при первой задаче.

### HF_TOKEN, GigaAM и Resemblyzer — не путать

| Задача | Нужен HF_TOKEN? | Чем делается |
|--------|-----------------|--------------|
| Распознавание **Whisper** (любая длина в лимите) | Нет | faster-whisper |
| **GigaAM**, файл ≤ ~25 с | Нет | `gigaam.transcribe` |
| **GigaAM**, файл > ~25 с | **Да** | Внутри GigaAM: сегментация `pyannote/segmentation-3.0` перед ASR |
| **Спикеры** после любого ASR | Нет (можно с токеном) | `auto`: pyannote если есть токен, иначе **Resemblyzer** |

**Resemblyzer** назначает роли **по уже готовому тексту** (шаг после распознавания). Он **не** режет длинное аудио для GigaAM и **не** заменяет segmentation-3.0 внутри длинного GigaAM. Без токена остаётся связка **Whisper + Resemblyzer** или **короткий GigaAM + Resemblyzer**.

## Два файла настроек

| Файл | Куда копировать | Что внутри |
|------|-----------------|------------|
| `backend/.env.example` | `backend/.env` | Пароль админа, токен Hugging Face, режим ролей. В Docker этот файл передаётся в контейнер |
| `compose.env.example` | `.env` в корне | Только порт, адрес публикации и при необходимости путь к кэшу моделей. Его читает Docker Compose на хосте |

Переменные `backend/.env`:

| Переменная | По умолчанию | Смысл |
|------------|--------------|--------|
| `ADMIN_USERNAME` | `admin` | Логин админки |
| `ADMIN_PASSWORD` | `admin` | Пароль. На сервере замените |
| `HF_TOKEN` | пусто | pyannote (спикеры), плюс **сегментация для длинного GigaAM** (> ~25 с). Как получить: **[HF_TOKEN.md](HF_TOKEN.md)**. Имя `HUGGING_FACE_HUB_TOKEN` тоже подходит |
| `DIARIZATION_BACKEND` | `auto` | `auto` — pyannote при наличии токена, иначе Resemblyzer; при сбое pyannote тоже Resemblyzer. `pyannote` — только pyannote. `resemblyzer` — только локальная кластеризация |
| `DIARIZATION_DEVICE` | `cpu` | Только CLI. Сайт берёт устройство из админки |
| `WHISPER_MODEL` | `medium` | Только CLI и `download_models.py` |
| `WHISPER_DEVICE` | `cpu` | Только CLI и `download_models.py` |
| `WHISPER_COMPUTE_TYPE` | `int8` | Тип вычислений Whisper на CPU. На CUDA сайт сам ставит `float16` |
| `FFMPEG_PATH`, `FFPROBE_PATH` | пусто | Явный путь, если программа не находится в `PATH` |

В Docker дополнительно заданы `DATA_DIR=/app/data`, `STATIC_DIR=/app/static`, `PORT=8080`. Менять их в обычной установке не нужно.

Каталог данных:

| Путь при локальном запуске | В контейнере | Содержимое |
|----------------------------|--------------|------------|
| `data/uploads/` | тот же путь в томе `stt-data` | Исходные файлы |
| `data/processed/` | том `stt-data` | WAV 16 кГц |
| `data/jobs.db` | том `stt-data` | Задачи SQLite |
| `data/system_settings.json` | том `stt-data` | Движок ASR, модель Whisper, устройство, лимит минут |
| `~/.cache/huggingface/` | `docker-bundled-models/huggingface` на хосте | Whisper, pyannote |
| `~/.cache/gigaam/` | внутри контейнера (том не задан) | Веса GigaAM |

Каталог `data/` в git не входит.

## Как устроена обработка

1. Файл сохраняется, проверяются размер и длительность.
2. ffmpeg приводит звук к моно WAV 16 кГц.
3. **ASR** по настройке админки: **Whisper** (язык авто, VAD через onnxruntime) или **GigaAM** (только русский; перед запуском — короткая проверка языка через Whisper tiny на CPU).
4. Каждому фрагменту текста назначается спикер: pyannote при токене и `auto`, иначе Resemblyzer (эмбеддинги по сегментам длиннее ~0.35 с, до 8 спикеров).
5. Результат попадает в базу и на страницу.

Прогресс идёт потоком SSE: `GET /api/transcriptions/{id}/events`. В событии есть `status`, `stage`, `message`.

Результат хранит сегменты (id, спикер, начало, конец, текст), отображаемые имена, движок ролей (`pyannote`, `resemblyzer` или `none`) и необязательное предупреждение `diarization_note`.

Один worker. Пока идёт распознавание, следующая загрузка ждёт слот. Отдельных учётных записей пользователей нет. Админская сессия хранится в памяти процесса.

## API

Локально backend доступен на `http://127.0.0.1:8000`. В режиме разработки Vite проксирует `/api`. В Docker сайт и API на одном порту.

| Метод и путь | Назначение |
|--------------|------------|
| `GET /api/health` | `{"ok": true}` |
| `GET /api/settings/public` | Движок ASR, модель, устройство, лимит минут, доступность GPU |
| `POST /api/admin/login` | Тело: `username`, `password`. Ответ: `token` |
| `GET /api/admin/settings` | Заголовок `X-Admin-Token` |
| `PATCH /api/admin/settings` | Тот же заголовок. Поля `asr_engine`, `model_tier`, `inference_device`, `max_duration_minutes` |
| `POST /api/transcriptions` | Поле формы `file`. Ответ 201, статус задачи |
| `GET /api/transcriptions/{id}` | Задача. В `result` лежит расшифровка, когда статус `done` |
| `GET /api/transcriptions/{id}/events` | Прогресс, SSE |
| `PATCH /api/transcriptions/{id}` | Имена спикеров и/или сегменты |
| `POST /api/transcriptions/{id}/rediarize` | Заново посчитать роли |
| `GET /api/transcriptions/{id}/audio` | Звук для плеера |
| `POST /api/transcriptions/{id}/export.txt` | TXT. Тело: `format` = `dialogue` или `timestamps`, `merge_adjacent` |
| `DELETE /api/transcriptions/{id}` | Удалить задачу и файлы, ответ 204 |

Ошибка — объект с `type`, `message` и иногда `extra`. Типы, которые видит интерфейс: `missing_filename`, `file_too_large`, `invalid_audio`, `audio_too_long`, `processing_failed`, `admin_unauthorized`, `admin_invalid_credentials`.

Пример смены настроек:

```json
{
  "asr_engine": "gigaam",
  "model_tier": "medium",
  "inference_device": "gpu",
  "max_duration_minutes": 60
}
```

`asr_engine`: `whisper` или `gigaam`. `model_tier`: `light`, `medium`, `heavy` (только Whisper). `inference_device`: `cpu` или `gpu`.

Публичные настройки дополнительно сообщают `gpu_available`, `gpu_backend` (`none`, `cuda` или `mps`) и границы ползунка длительности.

## Если что-то пошло не так

**После `./scripts/verify_deploy.sh` — крестики и предупреждения.** Пошагово по каждой строке вывода: [VERIFY_DEPLOY.md](VERIFY_DEPLOY.md).

**Контейнер сразу останавливается и в логе написано, что видеокарта недоступна.** На хосте выполните `nvidia-smi`. Затем `docker run --rm --gpus all nvidia/cuda:12.8.1-cudnn-runtime-ubuntu24.04 nvidia-smi`. Пока эта проверка не показывает карту, приложение её тоже не увидит. Дальше смотрите драйвер (CUDA Version 12.8+) и NVIDIA Container Toolkit. Запускать нужно файлом `docker-compose.gpu.yml`, не обычным `docker compose up`.

**Страница не открывается.** `docker compose -f docker-compose.gpu.yml ps`, порт `STT_PORT`, файрвол, значение `STT_BIND`. Если адрес публикации `127.0.0.1`, с другого компьютера сайт не откроется.

**Долго «Загрузка модели» или «В очереди».** Первая расшифровка без кэша качает Whisper или GigaAM; GigaAM на CPU может занимать 10–20 минут. В очереди одновременно считается один файл — пока идёт первая задача, следующие висят на ~10% («ожидание слота»). Смотрите `docker compose -f docker-compose.gpu.yml logs -f`.

**GigaAM / `gigaam_requires_token` на длинном файле.** См. [HF_TOKEN.md](HF_TOKEN.md), прогрейте `download_models.py` в контейнере — или используйте Whisper без токена.

**`Applying the VAD filter requires the onnxruntime package` (Whisper).** Переустановите зависимости backend / пересоберите образ; в `requirements-docker.txt` есть `onnxruntime`.

**`asr_language_unsupported` при GigaAM.** В записи не русский — переключите движок на Whisper в админке.

**GigaAM: `Model 'v3_e2e_rnnt' not found`.** Стоит старый пакет с PyPI (`0.1.0`). Локально: `cd backend && source .venv/bin/activate && pip install -r requirements.txt`. Docker: `docker compose -f docker-compose.gpu.yml up --build -d`.

**403 или ошибка скачивания модели.** Для выбранного размера нет весов в кэше, а huggingface.co недоступен. Положите кэш заранее (`./scripts/bundle_whisper_cache.sh` на машине, где модели уже скачаны) или откройте серверу доступ к Hugging Face и повторите задачу.

**Видео не загружается.** Нужна звуковая дорожка. В контейнере ffmpeg уже есть. Локально поставьте `brew install ffmpeg`.

**Один спикер на весь диалог.** На странице результата посмотрите движок ролей. `none` значит, что роли не посчитались: нажмите «Пересчитать роли». Resemblyzer хуже различает похожие голоса. Для pyannote настройте `HF_TOKEN` ([инструкция](HF_TOKEN.md)) и `DIARIZATION_BACKEND=auto`.

**Ошибка PyAV `metadata_errors`.** В `requirements-docker.txt` пакет `av` ограничен версиями `>=12,<16`. Пересоберите образ: `docker compose -f docker-compose.gpu.yml up --build -d`.

**Backend не видит пароль или токен.** Файл называется `backend/.env`. После правки пересоздайте контейнер: `docker compose -f docker-compose.gpu.yml up -d --force-recreate`. Локально перезапустите `./scripts/run_backend.sh`.

**Порты заняты локально.** `./scripts/stop.sh`, затем снова скрипты запуска.

**Проверка деплоя ругается на пароль `admin`.** Так и задумано. Задайте другой `ADMIN_PASSWORD` и пересоздайте контейнер.

**GPU видна, а расшифровка идёт на CPU.** В томе уже лежит `system_settings.json` с устройством CPU. Откройте ⚙ и включите видеокарту. Новый пустой том на CUDA сам стартует с GPU.
