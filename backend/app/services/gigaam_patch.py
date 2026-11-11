from __future__ import annotations

import logging
import os
import ssl
import urllib.parse
import urllib.request
from urllib.error import URLError

logger = logging.getLogger(__name__)

_SBER_CDN_SUFFIX = "sberdevices.ru"
_STRICT_SSL = os.environ.get("GIGAAM_STRICT_SSL", "").lower() in ("1", "true", "yes")


def _ssl_cert_error(exc: BaseException) -> bool:
    if isinstance(exc, ssl.SSLCertVerificationError):
        return True
    msg = str(exc).lower()
    return "certificate verify failed" in msg or "certificate has expired" in msg


def _urlopen_with_sber_fallback(url: str):
    import certifi

    ctx = ssl.create_default_context(cafile=certifi.where())
    try:
        return urllib.request.urlopen(url, context=ctx)
    except URLError as err:
        if _STRICT_SSL:
            raise
        host = urllib.parse.urlparse(url).hostname or ""
        if _SBER_CDN_SUFFIX not in host:
            raise
        reason = err.reason if isinstance(err.reason, BaseException) else err
        if not _ssl_cert_error(reason) and not _ssl_cert_error(err):
            raise
        logger.warning(
            "CDN GigaAM (%s): проверка SSL не прошла (%s). Повтор без проверки сертификата "
            "(сертификат CDN Сбера мог истечь). Чтобы отключить обход: GIGAAM_STRICT_SSL=1.",
            host,
            reason,
        )
        return urllib.request.urlopen(url, context=ssl._create_unverified_context())


def apply_gigaam_download_patch() -> None:
    """Patch gigaam downloads: certifi + fallback if Sber CDN SSL cert is expired."""
    import gigaam

    if getattr(gigaam, "_stt_download_patch_applied", False):
        return

    original = gigaam._download_file
    stock_urlopen = urllib.request.urlopen

    def patched_download(file_url: str, file_path: str, retries: int = gigaam._DOWNLOAD_RETRIES) -> str:
        def urlopen(url, *args, **kwargs):
            if args or kwargs:
                return stock_urlopen(url, *args, **kwargs)
            return _urlopen_with_sber_fallback(url)

        urllib.request.urlopen = urlopen  # type: ignore[assignment]
        try:
            return original(file_url, file_path, retries)
        finally:
            urllib.request.urlopen = stock_urlopen  # type: ignore[assignment]

    gigaam._download_file = patched_download
    gigaam._stt_download_patch_applied = True


def apply_gigaam_ffmpeg_patch() -> None:
    """GigaAM preprocess calls bare `ffmpeg`; use the same resolver as our audio pipeline."""
    import warnings
    from subprocess import CalledProcessError, run

    import gigaam
    import gigaam.preprocess as gp
    import torch
    from torch import Tensor

    if getattr(gp, "_stt_ffmpeg_patch_applied", False):
        return

    from app.services.audio import resolve_ffmpeg

    ffmpeg_bin = resolve_ffmpeg()

    def load_audio(audio_path: str, sample_rate: int = gp.SAMPLE_RATE) -> Tensor:
        cmd = [
            ffmpeg_bin,
            "-nostdin",
            "-threads",
            "0",
            "-i",
            audio_path,
            "-f",
            "s16le",
            "-ac",
            "1",
            "-acodec",
            "pcm_s16le",
            "-ar",
            str(sample_rate),
            "-",
        ]
        try:
            audio = run(cmd, capture_output=True, check=True).stdout
        except CalledProcessError as exc:
            raise RuntimeError("Failed to load audio") from exc

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=UserWarning)
            return torch.frombuffer(audio, dtype=torch.int16).float() / 32768.0

    def _bind(target: object) -> None:
        setattr(target, "load_audio", load_audio)

    _bind(gp)
    _bind(gigaam)
    import gigaam.model as gigaam_model
    import gigaam.vad_utils as gigaam_vad

    _bind(gigaam_model)
    _bind(gigaam_vad)
    gp._stt_ffmpeg_patch_applied = True


def apply_gigaam_patches() -> None:
    apply_gigaam_download_patch()
    apply_gigaam_ffmpeg_patch()
