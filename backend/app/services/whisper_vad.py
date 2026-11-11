from __future__ import annotations

import functools
import logging

logger = logging.getLogger(__name__)


@functools.lru_cache(maxsize=1)
def whisper_vad_filter_enabled() -> bool:
    """faster-whisper VAD needs a working onnxruntime; off if import fails."""
    try:
        import onnxruntime  # noqa: F401

        return True
    except Exception as exc:
        logger.warning("Whisper VAD disabled (onnxruntime unavailable): %s", exc)
        return False
