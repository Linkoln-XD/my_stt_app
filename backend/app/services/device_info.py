from __future__ import annotations

from typing import Literal

GpuBackend = Literal["none", "cuda", "mps"]


def detect_gpu_backend() -> GpuBackend:
    """Prefer NVIDIA CUDA; fall back to Apple MPS; else none."""
    try:
        import torch
    except Exception:
        return "none"

    try:
        if torch.cuda.is_available():
            return "cuda"
    except Exception:
        pass

    try:
        mps = getattr(torch.backends, "mps", None)
        if mps is not None and mps.is_available():
            return "mps"
    except Exception:
        pass

    return "none"


def gpu_available() -> bool:
    return detect_gpu_backend() != "none"
