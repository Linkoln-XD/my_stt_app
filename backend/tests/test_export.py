from app.models.schemas import TranscriptResult, TranscriptSegment
from app.services.export import export_txt


def test_export_dialogue_and_timestamps():
    result = TranscriptResult(
        duration_sec=10.0,
        speakers={"SPEAKER_00": "А", "SPEAKER_01": "Б"},
        segments=[
            TranscriptSegment(
                id="1",
                speaker_id="SPEAKER_00",
                start=1.0,
                end=2.0,
                text="Привет",
            ),
            TranscriptSegment(
                id="2",
                speaker_id="SPEAKER_01",
                start=2.5,
                end=4.0,
                text="Ответ",
            ),
        ],
    )
    dialogue = export_txt(result, "dialogue", merge_adjacent=False)
    assert "А: Привет" in dialogue
    assert "Б: Ответ" in dialogue

    ts = export_txt(result, "timestamps", merge_adjacent=False)
    assert "[00:00:01]" in ts
    assert "А: Привет" in ts
