#!/usr/bin/env sh
set -eu

DATA="${DATA_DIR:-/app/data}"
mkdir -p "${DATA}/uploads" "${DATA}/processed"

if [ "${STT_REQUIRE_GPU:-}" = "1" ]; then
  python - <<'PY'
import sys

try:
    import torch
except Exception as exc:
    print(f"Не удалось импортировать torch: {exc}", file=sys.stderr)
    sys.exit(1)

try:
    cuda_ok = bool(torch.cuda.is_available())
except Exception as exc:
    print(f"Ошибка проверки CUDA: {exc}", file=sys.stderr)
    sys.exit(1)

ct_ok = False
ct_error = ""
try:
    import ctranslate2

    ctranslate2.get_supported_compute_types("cuda")
    ct_ok = True
except Exception as exc:
    ct_error = str(exc)

if not cuda_ok or not ct_ok:
    print("Этот образ требует NVIDIA GPU, но видеокарта в контейнере недоступна.", file=sys.stderr)
    if ct_error:
        print(f"CTranslate2: {ct_error}", file=sys.stderr)
    print(
        "Проверьте на сервере: nvidia-smi, пакет nvidia-container-toolkit, "
        "запуск через docker compose -f docker-compose.gpu.yml up --build -d.",
        file=sys.stderr,
    )
    sys.exit(1)

print(f"CUDA OK: {torch.cuda.get_device_name(0)}", flush=True)
PY
fi

cd /app/backend
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8080}"
