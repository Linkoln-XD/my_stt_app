# Развёртывание на сервере (Docker)

Пошаговая инструкция для администратора: **один контейнер**, один внешний порт, веб-интерфейс и API вместе.

> **Два файла настроек:**  
> - `backend/.env` — пароль админа, Whisper, опционально Hugging Face.  
> - `.env` в **корне** проекта (рядом с `docker-compose.yml`) — только порт `STT_PORT` и путь к кэшу моделей.

---

## Что понадобится на сервере

| Требование | Комментарий |
|------------|-------------|
| **Linux x86_64 или arm64** (или macOS с Docker Desktop) | RAM **8 GB+** рекомендуется |
| **Docker Engine 24+** | [Установка](https://docs.docker.com/engine/install/) |
| **Docker Compose v2** | Пакет `docker-compose-plugin` или Docker Desktop |
| **Диск** | **15–25 GB** свободно (образ PyTorch + модель Whisper + данные) |
| **Сеть** | Интернет для **первой** сборки образа; для Whisper без готового кэша — также при первой расшифровке |
| **Порт TCP** | По умолчанию **8080** (настраивается) |

Проверка:

```bash
docker --version
docker compose version
```

На Linux пользователь должен быть в группе `docker` **или** команды ниже с `sudo`:

```bash
sudo usermod -aG docker "$USER"   # затем перелогиниться
```

---

## Шаг 1. Получить проект

**Из git:**

```bash
sudo mkdir -p /opt && sudo chown "$USER" /opt
cd /opt
git clone <URL-репозитория> my_stt_app
cd my_stt_app
```

**Из архива:** распакуйте в каталог, например `/opt/my_stt_app`, и выполните `cd /opt/my_stt_app`.

---

## Шаг 2. Пароль администратора

```bash
cp backend/.env.example backend/.env
nano backend/.env
```

**Обязательно задайте:**

```env
ADMIN_USERNAME=admin
ADMIN_PASSWORD=ваш_надёжный_пароль
```

Эти данные — вход в **⚙ Настройки** на главной (лимит длительности 10–120 мин и т.д.).

Остальное можно не менять на первом запуске. Позже: `WHISPER_MODEL=medium`, `HF_TOKEN=...` (см. [SETUP.md](./SETUP.md)).

---

## Шаг 3. Порт и (опционально) путь к кэшу Whisper

```bash
cp compose.env.example .env
nano .env
```

Минимальный `.env` в корне:

```env
STT_PORT=8080
```

Другой внешний порт, например **9000**:

```env
STT_PORT=9000
```

Внутри контейнера приложение всегда слушает **8080**; Docker пробрасывает его на `STT_PORT`.

**Файрвол** (пример):

```bash
sudo ufw allow 8080/tcp
sudo ufw reload
```

---

## Шаг 4. Кэш модели Whisper (выберите один вариант)

Модель **medium** (~1.5 GB) нужна для распознавания. Без кэша она скачается при **первой** расшифровке (долго).

### Вариант A — сервер **только с интернетом** (проще)

Создайте пустой каталог для кэша (Compose смонтирует его в контейнер):

```bash
mkdir -p docker-bundled-models/huggingface
```

При первой успешной расшифровке модель сохранится **в этой папке** на диске сервера; повторно качать не нужно.

### Вариант B — перенести кэш с другой машины (быстрее)

На машине, где Whisper уже скачан (например, после локального STT):

```bash
./scripts/bundle_whisper_cache.sh
```

Скопируйте на сервер каталог **`docker-bundled-models/huggingface`** (≈1.5 GB) — рядом с `docker-compose.yml`, в тот же путь внутри проекта.

Либо укажите свой путь в корневом `.env`:

```env
STT_HF_CACHE_HOST=/srv/stt/huggingface
```

(каталог на сервере должен существовать и содержать кэш Hugging Face).

---

## Шаг 5. Собрать образ и запустить

Из **корня** проекта (`my_stt_app`, где лежит `docker-compose.yml`):

```bash
docker compose up --build -d
```

Первая сборка часто занимает **15–40 минут** (скачивание базового образа, PyTorch, зависимостей). Это нормально.

Проверка:

```bash
docker compose ps
./scripts/verify_deploy.sh
```

Или вручную (подставьте свой `STT_PORT`):

```bash
curl -s http://127.0.0.1:8080/api/health
```

Ожидается: `{"ok":true}`.

Если контейнер не стартует:

```bash
docker compose logs --tail 100
```

---

## Шаг 6. Открыть в браузере

```text
http://<IP-или-домен-сервера>:<STT_PORT>/
```

Пример: `http://192.168.1.100:8080/`

На самом сервере: `http://127.0.0.1:8080/`.

---

## Шаг 7. Настройки в интерфейсе

1. Главная страница → **⚙** (шапка справа).  
2. Логин и пароль из **`backend/.env`**.  
3. Ползунок **10–120 мин** — лимит длительности файла → **«Применить для всех»**.

Подробнее: [ADMIN.md](./ADMIN.md).

---

## Управление

| Действие | Команда (из корня проекта) |
|----------|----------------------------|
| Статус | `docker compose ps` |
| Логи | `docker compose logs -f` |
| Остановить | `docker compose down` |
| Запустить снова | `docker compose up -d` |
| Обновить код и пересобрать | `git pull && docker compose up --build -d` |

**Данные:** Docker-том `stt-data` (загрузки, `jobs.db`, `system_settings.json`).  
**Кэш Whisper:** папка `docker-bundled-models/huggingface` на хосте (или путь из `STT_HF_CACHE_HOST`).

`docker compose down` **не удаляет** том `stt-data`.

После смены `backend/.env`:

```bash
docker compose up -d --force-recreate
```

---

## Проверка после установки

```bash
./scripts/verify_deploy.sh
```

Скрипт проверяет Docker, наличие `.env`, кэш Whisper и `GET /api/health`.

---

## Типичные проблемы

| Симптом | Что сделать |
|---------|-------------|
| `permission denied` при docker | `sudo` или добавить пользователя в группу `docker` |
| Страница не открывается | `docker compose ps`, фаервол, верный `STT_PORT` |
| Долго «В очереди» / «Загрузка модели» | Первый запуск без кэша — смотреть `docker compose logs -f`; нужен интернет |
| Ошибка при загрузке файла | Логи: `docker compose logs -f`; см. [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) |
| Нет `rsync` при bundle | Скрипт использует `cp`; или `sudo apt install rsync` |

---

## Безопасность

- Смените `ADMIN_PASSWORD` до выдачи URL другим людям.  
- Для доступа из интернета — **HTTPS** (nginx/Caddy) и ограничение по IP/VPN.  
- Авторизации пользователей нет: любой с URL может загружать файлы в пределах лимита.

---

## Шпаргалка (копировать блок целиком)

```bash
cd /opt
git clone <URL-репозитория> my_stt_app
cd my_stt_app

cp backend/.env.example backend/.env
# nano backend/.env  → ADMIN_PASSWORD

cp compose.env.example .env
# nano .env          → STT_PORT=8080

mkdir -p docker-bundled-models/huggingface
# опционально: ./scripts/bundle_whisper_cache.sh  — если кэш уже есть на этой машине

docker compose up --build -d
./scripts/verify_deploy.sh

# браузер: http://<IP-сервера>:8080/
```
