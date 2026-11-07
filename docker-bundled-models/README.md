# Кэш Whisper для Docker

Compose монтирует каталог `huggingface/` в контейнер как `/root/.cache/huggingface`.

На сервере без готового кэша достаточно создать пустую папку. Модель скачается при первой расшифровке и останется здесь:

```bash
mkdir -p docker-bundled-models/huggingface
```

Чтобы перенести кэш с машины, где модели уже скачаны:

```bash
./scripts/bundle_whisper_cache.sh
```

Как это связано с деплоем: [docs/GUIDE.md](../docs/GUIDE.md).
