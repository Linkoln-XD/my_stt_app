from __future__ import annotations

from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class TranscriptSegment(BaseModel):
    id: str
    speaker_id: str
    start: float
    end: float
    text: str


class TranscriptResult(BaseModel):
    duration_sec: float
    language: Optional[str] = None
    speakers: Dict[str, str] = Field(default_factory=dict)
    segments: List[TranscriptSegment] = Field(default_factory=list)
    diarization_engine: Optional[str] = None
    diarization_note: Optional[str] = None


class JobResponse(BaseModel):
    id: str
    status: str
    stage: str
    message: str
    original_filename: str
    error: Optional[str] = None
    created_at: Optional[str] = None
    result: Optional[TranscriptResult] = None


class UpdateTranscriptRequest(BaseModel):
    speakers: Optional[Dict[str, str]] = None
    segments: Optional[List[TranscriptSegment]] = None


ExportFormat = Literal["dialogue", "timestamps"]
