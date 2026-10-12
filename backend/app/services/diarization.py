from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import numpy as np
from resemblyzer import VoiceEncoder, preprocess_wav
from resemblyzer.hparams import sampling_rate as RESEMBLYZER_SR
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import silhouette_score

from app.config import settings

logger = logging.getLogger(__name__)

_voice_encoder: Optional[VoiceEncoder] = None

MIN_SEGMENT_SEC = 0.35
MAX_SPEAKERS = 8
MIN_SILHOUETTE = 0.12


def _estimate_num_speakers(embeddings: np.ndarray) -> int:
    n = len(embeddings)
    if n < 4:
        return 1

    best_k = 1
    best_score = -1.0
    min_cluster = max(2, int(n * 0.08))
    max_k = min(MAX_SPEAKERS, n // 2)

    for k in range(2, max_k + 1):
        labels = AgglomerativeClustering(
            n_clusters=k,
            metric="cosine",
            linkage="average",
        ).fit_predict(embeddings)
        counts = np.bincount(labels)
        if counts.min() < min_cluster:
            continue
        score = float(silhouette_score(embeddings, labels, metric="cosine"))
        if score > best_score:
            best_score = score
            best_k = k

    if best_k > 1 and best_score >= MIN_SILHOUETTE:
        return best_k
    return 1


def _encoder() -> VoiceEncoder:
    global _voice_encoder
    if _voice_encoder is None:
        _voice_encoder = VoiceEncoder()
    return _voice_encoder


def diarize_by_segments_resemblyzer(
    wav_path: Path,
    asr_segments: list[tuple[float, float, str]],
) -> list[tuple[float, float, str, str]]:
    """Cluster per-utterance embeddings (offline, no Hugging Face token)."""
    wav = preprocess_wav(wav_path)
    encoder = _encoder()

    embeddings: list[np.ndarray] = []
    indexed: list[int] = []

    for i, (start, end, _text) in enumerate(asr_segments):
        if end - start < MIN_SEGMENT_SEC:
            continue
        start_i = int(start * RESEMBLYZER_SR)
        end_i = int(end * RESEMBLYZER_SR)
        chunk = wav[start_i:end_i]
        if len(chunk) < int(RESEMBLYZER_SR * MIN_SEGMENT_SEC):
            continue
        embeddings.append(encoder.embed_utterance(chunk))
        indexed.append(i)

    if not embeddings:
        return [(s, e, t, "SPEAKER_00") for s, e, t in asr_segments]

    matrix = np.vstack(embeddings)
    num_speakers = _estimate_num_speakers(matrix)
    if num_speakers <= 1:
        labels = np.zeros(len(embeddings), dtype=int)
    else:
        labels = AgglomerativeClustering(
            n_clusters=num_speakers,
            metric="cosine",
            linkage="average",
        ).fit_predict(matrix)

    index_to_speaker = {
        idx: f"SPEAKER_{int(label):02d}" for idx, label in zip(indexed, labels)
    }

    assigned: list[tuple[float, float, str, str]] = []
    last = "SPEAKER_00"
    for i, (start, end, text) in enumerate(asr_segments):
        speaker = index_to_speaker.get(i, last)
        last = speaker
        assigned.append((start, end, text, speaker))
    return assigned


_pyannote_pipeline = None


def run_pyannote(wav_path: Path) -> list[tuple[float, float, str]]:
    global _pyannote_pipeline
    from pyannote.audio import Pipeline
    import torch

    if not settings.hf_token:
        raise RuntimeError("HF_TOKEN is not configured")

    if _pyannote_pipeline is None:
        _pyannote_pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            token=settings.hf_token,
        )
        device_name = settings.diarization_device
        if device_name == "auto":
            device_name = "cpu"
        _pyannote_pipeline.to(torch.device(device_name))
    pipeline = _pyannote_pipeline

    diarization = pipeline(str(wav_path))
    turns: list[tuple[float, float, str]] = []
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        turns.append((turn.start, turn.end, str(speaker)))
    return turns
