# Кэш Whisper для Docker

Compose монтирует каталог `huggingface/` в контейнер как `/root/.cache/huggingface`.

**На сервере без готового кэша** (достаточно для старта):

```bash
mkdir -p docker-bundled-models/huggingface
```

Модель скачается при первой расшифровке и останется в этой папке.

**Скопировать с другой машины** (где уже был STT):

```bash
./scripts/bundle_whisper_cache.sh
```

Подробнее: [docs/DEPLOYMENT.md](../docs/DEPLOYMENT.md).
