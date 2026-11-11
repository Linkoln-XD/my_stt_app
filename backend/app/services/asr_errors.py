from __future__ import annotations


class AsrLanguageUnsupportedError(ValueError):
    """GigaAM is Russian-only; detected another language."""


class GigaamModelDownloadError(RuntimeError):
    """GigaAM weights could not be downloaded or loaded."""


class GigaamRequiresTokenError(RuntimeError):
    """Long-form GigaAM needs HF_TOKEN for pyannote segmentation."""
