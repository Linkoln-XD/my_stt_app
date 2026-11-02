# Админ-панель и системные настройки

## Назначение

Администратор задаёт **глобальные** параметры для всех пользователей сервиса:

| Параметр | Поведение |
|----------|-----------|
| **Модель** (лёгкая / средняя / тяжёлая) | Выбор Whisper для всех новых расшифровок: `small` / `medium` / `large-v3`. При смене tier модель перезагружается на следующем job. |
| **Устройство** (процессор / видеокарта) | По умолчанию CPU. GPU доступна при **CUDA** (приоритет) или **Apple MPS**. На CUDA: Whisper + pyannote на GPU; на MPS: pyannote на Metal, Whisper на CPU (CTranslate2 без Metal). Если GPU нет — опция disabled, сохранённый `gpu` сбрасывается в `cpu`. |
| **Макс. длительность** | Лимит в минутах: **10–120** (ползунок в админке). Применяется при загрузке и в пайплайне. |

Настройки хранятся в `data/system_settings.json` (не в git).

## Доступ из UI

1. На **главной странице** нажмите **⚙** в правом верхнем углу.
2. При **первом** открытии за сессию браузера (до F5) — форма логина/пароля.
3. После успешного входа флаг хранится в `sessionStorage` (`stt_admin_unlocked`), токен — `stt_admin_token`.
4. Обновление страницы (F5) снова запросит пароль.

## Учётные данные

На сервере с Docker файл монтируется через `env_file` в `docker-compose.yml`. После смены пароля выполните `docker compose up -d --force-recreate`.

Задаются в `backend/.env`:

```env
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin
```

**Обязательно смените пароль** в любой среде, доступной не только вам.

## API

| Метод | Путь | Auth |
|-------|------|------|
| GET | `/api/settings/public` | Нет |
| POST | `/api/admin/login` | Body: username, password |
| GET | `/api/admin/settings` | Header `X-Admin-Token` |
| PATCH | `/api/admin/settings` | Header `X-Admin-Token` |

Пример PATCH:

```json
{
  "model_tier": "heavy",
  "inference_device": "gpu",
  "max_duration_minutes": 15
}
```

Токен сессии выдаётся на 8 часов (in-memory на процессе uvicorn; перезапуск backend сбрасывает сессии).

## Безопасность

- Сервис рассчитан на **localhost**. Не выставляйте админку в интернет без HTTPS, rate limit и сильного пароля.
- Токен админа не используйте в публичных клиентах.
