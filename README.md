# STT App

Локальное веб-приложение для расшифровки аудио и видео с разделением по спикерам. Русский и английский определяются автоматически. Загрузили файл, получили текст, ушли: история прошлых загрузок на главной не хранится.

Текущая версия — **0.3.0**. Полное руководство: [docs/GUIDE.md](docs/GUIDE.md).

## Локальный запуск (macOS)

Нужны [Homebrew](https://brew.sh), Python 3.12, ffmpeg и Node.js 20+.

```bash
brew install python@3.12 ffmpeg node

cp backend/.env.example backend/.env
./scripts/run_backend.sh     # http://127.0.0.1:8000
./scripts/run_frontend.sh    # http://127.0.0.1:5173
```

Откройте **http://127.0.0.1:5173**. Остановка: `./scripts/stop.sh`.

Два процесса запускаются в двух терминалах. Первый запуск backend сам создаёт `backend/.venv` и ставит зависимости.

## Сервер с NVIDIA GPU

Образ `Dockerfile.gpu`: CUDA 12.8, cuDNN 9, PyTorch cu128. Whisper и pyannote идут на видеокарту, когда в админке выбрано GPU. Карты от Turing и новее (RTX 20-й серии, T4, A10, L4, A100, RTX 30/40, H100, Blackwell). На хосте — драйвер с поддержкой CUDA 12.8 (`nvidia-smi` показывает CUDA Version 12.8 или выше) и [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html).

```bash
cp backend/.env.example backend/.env
# В backend/.env задайте свой ADMIN_PASSWORD. Значение admin проверка не пропустит.

cp compose.env.example .env
mkdir -p docker-bundled-models/huggingface

docker compose -f docker-compose.gpu.yml up --build -d
./scripts/verify_deploy.sh --gpu
```

Сайт: **http://IP-сервера:8080/**. Первая сборка долгая: качаются CUDA-образ, PyTorch и зависимости.

Подробности, кэш модели, HTTPS и типичные сбои — в [docs/GUIDE.md](docs/GUIDE.md).

## Локальная проверка Docker без GPU

На Mac видеокарту в контейнер не пробросить. Этот образ нужен, чтобы проверить сборку, и для сервера без NVIDIA. На сервере с GPU используйте команды из раздела выше.

```bash
cp backend/.env.example backend/.env   # свой ADMIN_PASSWORD
cp compose.env.example .env
mkdir -p docker-bundled-models/huggingface
docker compose up --build -d
./scripts/verify_deploy.sh
```

Сайт: **http://127.0.0.1:8080/**.

## Возможности

- Загрузка аудио (MP3, WAV, M4A, OGG) и видео (AVI, MKV, MP4, MOV, WebM). Берётся первая аудиодорожка.
- Распознавание faster-whisper и роли спикеров: pyannote при наличии `HF_TOKEN`, иначе локальный Resemblyzer.
- Плеер, правка текста и имён, поиск, пересчёт ролей без повторного распознавания, экспорт TXT.
- Админка (кнопка ⚙): модель Whisper, устройство CPU/GPU, лимит длительности 10–120 минут.

Одновременно обрабатывается один файл.
