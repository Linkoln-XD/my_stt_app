from app.models.schemas import ExportFormat, TranscriptResult


def _speaker_label(result: TranscriptResult, speaker_id: str) -> str:
    return result.speakers.get(speaker_id) or speaker_id


def _format_timestamp(seconds: float) -> str:
    total_ms = int(round(seconds * 1000))
    hours, rem_ms = divmod(total_ms, 3600 * 1000)
    minutes, rem_ms = divmod(rem_ms, 60 * 1000)
    secs, _ms = divmod(rem_ms, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def export_txt(result: TranscriptResult, fmt: ExportFormat, merge_adjacent: bool = True) -> str:
    segments = list(result.segments)
    if merge_adjacent and segments:
        merged = [segments[0].model_copy()]
        for seg in segments[1:]:
            prev = merged[-1]
            if seg.speaker_id == prev.speaker_id:
                prev.end = seg.end
                prev.text = f"{prev.text.rstrip()} {seg.text.lstrip()}".strip()
            else:
                merged.append(seg.model_copy())
        segments = merged

    lines: list[str] = []
    for seg in segments:
        label = _speaker_label(result, seg.speaker_id)
        text = seg.text.strip()
        if not text:
            continue
        if fmt == "dialogue":
            lines.append(f"{label}: {text}")
        elif fmt == "timestamps":
            ts = _format_timestamp(seg.start)
            lines.append(f"[{ts}] {label}: {text}")
        else:
            raise ValueError(f"Unknown export format: {fmt}")

    return "\n".join(lines).strip() + "\n"
