from pathlib import Path

import pytest

from app.services.asr import run_asr
from app.services.asr_errors import AsrLanguageUnsupportedError
from app.services.system_settings import SystemSettings, save_system_settings


def test_asr_dispatches_whisper(tmp_path, monkeypatch):
    monkeypatch.setattr("app.services.system_settings.settings.data_dir", tmp_path)
    save_system_settings(SystemSettings(asr_engine="whisper", max_duration_minutes=30))

    wav = tmp_path / "x.wav"
    wav.write_bytes(b"x")

    monkeypatch.setattr(
        "app.services.asr.run_whisper_asr",
        lambda _p, _cb=None: ([(0.0, 1.0, "hi")], "en"),
    )
    segs, lang = run_asr(wav, 1.0)
    assert segs[0][2] == "hi"
    assert lang == "en"


def test_gigaam_rejects_non_russian(tmp_path, monkeypatch):
    monkeypatch.setattr("app.services.system_settings.settings.data_dir", tmp_path)
    save_system_settings(SystemSettings(asr_engine="gigaam", max_duration_minutes=30))

    wav = tmp_path / "x.wav"
    wav.write_bytes(b"x")

    monkeypatch.setattr("app.services.asr.probe_speech_language", lambda _p: "en")
    with pytest.raises(AsrLanguageUnsupportedError):
        run_asr(wav, 10.0)


def test_gigaam_runs_when_russian(tmp_path, monkeypatch):
    monkeypatch.setattr("app.services.system_settings.settings.data_dir", tmp_path)
    save_system_settings(SystemSettings(asr_engine="gigaam", max_duration_minutes=30))

    wav = tmp_path / "x.wav"
    wav.write_bytes(b"x")

    monkeypatch.setattr("app.services.asr.probe_speech_language", lambda _p: "ru")
    monkeypatch.setattr(
        "app.services.asr.run_gigaam_asr",
        lambda _p, _d, _cb=None: ([(0.0, 2.0, "привет")], "ru"),
    )
    segs, lang = run_asr(wav, 2.0)
    assert segs[0][2] == "привет"
    assert lang == "ru"
