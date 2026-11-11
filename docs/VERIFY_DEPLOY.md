# Проверка деплоя (`verify_deploy.sh`)

После поднятия контейнера запустите из **корня репозитория**:

```bash
./scripts/verify_deploy.sh          # CPU: docker-compose.yml
./scripts/verify_deploy.sh --gpu    # NVIDIA: docker-compose.gpu.yml
```

Скрипт **ничего не чинит сам** — только печатает ✓ / ⚠ / ✗ и завершается с кодом **0** (успех) или **1** (есть ✗). Ниже — что означает каждое сообщение и как исправить.

Связанные разделы: [GUIDE.md — деплой GPU](GUIDE.md), [README](../README.md).

## Легенда

| Символ | Значение |
|--------|----------|
| ✓ | Проверка пройдена |
| ⚠ | Предупреждение — деплой может работать, но лучше устранить |
| ✗ | Ошибка — скрипт завершится с кодом 1 |

---

## Ошибки (✗)

### `docker not found`

**Причина:** на хосте нет Docker CLI.

**Исправление:**

- Linux: установите [Docker Engine](https://docs.docker.com/engine/install/) (пакет `docker.io` или официальный репозиторий Docker).
- Проверка: `docker --version`.
- Убедитесь, что пользователь в группе `docker` или запускайте команды с правами, которые приняты у вас на сервере.

---

### `docker compose not found`

**Причина:** нет плагина Compose V2 (`docker compose`).

**Исправление:**

- Установите Docker Compose plugin вместе с Docker Engine (актуальные инструкции Docker для вашего дистрибутива).
- Проверка: `docker compose version` (не путать со старым `docker-compose` как отдельным бинарником — он тоже часто работает, но скрипт проверяет именно `docker compose`).

---

### `GPU compose files missing` (только с `--gpu`)

**Причина:** в каталоге проекта нет `Dockerfile.gpu` или `docker-compose.gpu.yml`.

**Исправление:**

- Запускайте скрипт из **клонированного репозитория**, не из урезанной копии.
- `git pull` / восстановите файлы из репозитория.
- Для CPU без GPU используйте `./scripts/verify_deploy.sh` **без** `--gpu`.

---

### `missing backend/.env` …

**Причина:** нет файла настроек приложения.

**Исправление:**

```bash
cp backend/.env.example backend/.env
```

Задайте как минимум `ADMIN_PASSWORD` (не `admin` на сервере). При необходимости — `HF_TOKEN` ([HF_TOKEN.md](HF_TOKEN.md)).

Затем:

```bash
docker compose -f docker-compose.gpu.yml up -d --force-recreate
# или без --gpu:
docker compose up -d --force-recreate
```

---

### `ADMIN_PASSWORD in backend/.env is still the default`

**Причина:** пароль админки остался `admin` (или пустой). Для сервера проверка намеренно строгая.

**Исправление:**

1. В `backend/.env`: `ADMIN_PASSWORD=длинный_секретный_пароль`
2. Пересоздайте контейнер:  
   `docker compose -f docker-compose.gpu.yml up -d --force-recreate`
3. Повторите `./scripts/verify_deploy.sh --gpu`

Логин по умолчанию: `ADMIN_USERNAME=admin` (можно сменить в том же файле).

---

### `container not running` …

**Причина:** сервис `stt` не в состоянии running.

**Исправление:**

1. Поднимите стек (из корня репозитория):

   ```bash
   docker compose -f docker-compose.gpu.yml up --build -d
   ```

2. Статус: `docker compose -f docker-compose.gpu.yml ps`
3. Логи: `docker compose -f docker-compose.gpu.yml logs --tail 100`
4. Типичные причины падения GPU-контейнера:
   - нет GPU / toolkit → см. **«GPU-образ запущен, но CUDA в контейнере не видна»** ниже;
   - ошибка при старте Python → смотрите traceback в логах.

---

### `health check failed on port …`

**Причина:** контейнер вроде запущен, но `GET http://127.0.0.1:PORT/api/health` не вернул `{"ok": true}`.

**Исправление:**

1. Узнайте порт: корневой `.env` → `STT_PORT` (по умолчанию **8080**). Скрипт дергает **127.0.0.1 на хосте**, не внутри контейнера.
2. Вручную: `curl -v http://127.0.0.1:8080/api/health`
3. Если connection refused:
   - compose не пробросил порт — проверьте `ports` и `STT_BIND` в `.env`;
   - приложение ещё стартует — подождите и смотрите `logs -f` (первый запуск torch может быть долгим).
4. Если 502/таймаут — смотрите логи контейнера; пересоберите при смене зависимостей: `up --build -d`.

Подробнее: [GUIDE.md — «Страница не открывается»](GUIDE.md).

---

### `GET /api/settings/public failed` (только с `--gpu`)

**Причина:** health мог пройти, но публичный API настроек недоступен (редко).

**Исправление:**

1. `curl -sf http://127.0.0.1:8080/api/settings/public` — смотрите код и тело ответа.
2. Логи uvicorn: `docker compose -f docker-compose.gpu.yml logs -f`
3. Перезапуск: `up -d --force-recreate`; при повреждённых данных — бэкап тома `stt-data` перед экспериментами.

---

### `GPU-образ запущен, но CUDA в контейнере не видна` …

**Причина:** в API `gpu_available` не `true` или `gpu_backend` не `cuda` (запускали CPU-compose, нет драйвера, нет NVIDIA Container Toolkit, GPU не проброшен).

**Исправление:**

1. На **хосте**: `nvidia-smi` (драйвер, CUDA Version ≥ 12.8 для образа GPU).
2. Проброс в Docker:

   ```bash
   docker run --rm --gpus all nvidia/cuda:12.8.1-cudnn-runtime-ubuntu24.04 nvidia-smi
   ```

   Должна быть та же карта. Если нет — [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html), перезапуск демона Docker.
3. Запуск **только** через `docker compose -f docker-compose.gpu.yml up -d`, не `docker compose up` (CPU-файл).
4. После правок: `logs -f` — при `STT_REQUIRE_GPU=1` контейнер сам пишет причину, если CUDA недоступна.

Подробнее: [GUIDE.md — «Контейнер сразу останавливается…»](GUIDE.md).

---

## Предупреждения (⚠)

### `no root .env — using STT_PORT=8080`

**Смысл:** нет файла `.env` в **корне** репозитория (порт и `STT_BIND` для Compose).

**Исправление (по желанию):**

```bash
cp compose.env.example .env
```

Задайте `STT_PORT`, при публикации только на localhost — `STT_BIND=127.0.0.1`. Перезапуск: `docker compose … up -d`.

---

### `Whisper cache not found — the first transcription downloads the model`

**Смысл:** на хосте нет заранее скачанной **medium** в `docker-bundled-models/huggingface` (или путь из `STT_HF_CACHE_HOST`).

**Исправление (по желанию, для офлайн/быстрого старта):**

```bash
mkdir -p docker-bundled-models/huggingface
docker compose -f docker-compose.gpu.yml exec stt python scripts/download_models.py --whisper-only
```

Или перенесите кэш с другой машины: [GUIDE.md — кэш Whisper](GUIDE.md).

Первая расшифровка **без** кэша тоже работает, но потребует интернет и время.

---

### `CUDA видна, но inference_device сейчас «cpu»` …

**Смысл:** GPU доступна, но в томе `stt-data` уже сохранён `system_settings.json` с **CPU** (скрипт том не перезаписывает).

**Исправление:**

1. Откройте сайт → ⚙ админка → **Видеокарта (GPU)** → сохранить.
2. Или на чистой установке удалите том (осторожно: потеря задач/настроек):  
   `docker compose -f docker-compose.gpu.yml down` и при необходимости сброс тома по вашей политике бэкапов.

См. [GUIDE.md — «GPU видна, а расшифровка идёт на CPU»](GUIDE.md).

---

## Успешные проверки (✓)

| Сообщение | Комментарий |
|-----------|-------------|
| `docker installed` / `docker compose available` | Окружение готово |
| `GPU compose files present` | Релевантно только `--gpu` |
| `backend/.env exists` | Файл на месте |
| `ADMIN_PASSWORD is not the default` | Пароль для сервера приемлем |
| `root .env exists` | Порт/публикация заданы |
| `Whisper medium cache present` | Прогрет кэш HF |
| `container is running` | Сервис `stt` up |
| `health OK → http://127.0.0.1:PORT/` | API жив |
| `NVIDIA CUDA is visible in the container` | GPU-режим для CUDA |
| `inference device is gpu` | И настройки тоже на GPU |

После всех ✓ без ✗ откройте в браузере `http://<хост>:PORT/` (с учётом `STT_BIND` и файрвола).

## Повторная проверка

```bash
./scripts/verify_deploy.sh --gpu
echo $?   # 0 — успех
```

При смене `backend/.env` или `.env` всегда делайте `docker compose … up -d --force-recreate`, иначе контейнер может не увидеть новые переменные.
