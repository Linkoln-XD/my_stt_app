import pytest

from app.services.system_settings import (
    MAX_DURATION_MINUTES,
    MIN_DURATION_MINUTES,
    TIER_TO_WHISPER,
    SystemSettings,
    get_max_duration_sec,
    load_system_settings,
    resolve_diarization_torch_device,
    resolve_whisper_model_name,
    resolve_whisper_runtime,
    save_system_settings,
)


def test_save_and_load_duration(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "app.services.system_settings.settings.data_dir",
        tmp_path,
    )
    save_system_settings(SystemSettings(model_tier="light", max_duration_minutes=15))
    loaded = load_system_settings()
    assert loaded.max_duration_minutes == 15
    assert get_max_duration_sec() == 15 * 60


def test_duration_bounds(tmp_path, monkeypatch):
    monkeypatch.setattr("app.services.system_settings.settings.data_dir", tmp_path)
    save_system_settings(SystemSettings(model_tier="medium", max_duration_minutes=120))
    assert load_system_settings().max_duration_minutes == MAX_DURATION_MINUTES
    save_system_settings(SystemSettings(model_tier="medium", max_duration_minutes=10))
    assert load_system_settings().max_duration_minutes == MIN_DURATION_MINUTES


def test_load_clamps_legacy_below_min(tmp_path, monkeypatch):
    monkeypatch.setattr("app.services.system_settings.settings.data_dir", tmp_path)
    path = tmp_path / "system_settings.json"
    path.write_text('{"model_tier": "medium", "max_duration_minutes": 5}', encoding="utf-8")
    assert load_system_settings().max_duration_minutes == MIN_DURATION_MINUTES


def test_save_rejects_out_of_range(tmp_path, monkeypatch):
    monkeypatch.setattr("app.services.system_settings.settings.data_dir", tmp_path)
    with pytest.raises(Exception):
        save_system_settings(SystemSettings(model_tier="medium", max_duration_minutes=9))


def test_resolve_whisper_model_follows_tier(tmp_path, monkeypatch):
    monkeypatch.setattr("app.services.system_settings.settings.data_dir", tmp_path)
    for tier, expected in TIER_TO_WHISPER.items():
        save_system_settings(SystemSettings(model_tier=tier, max_duration_minutes=30))
        assert resolve_whisper_model_name() == expected


def test_gpu_normalized_to_cpu_when_unavailable(tmp_path, monkeypatch):
    monkeypatch.setattr("app.services.system_settings.settings.data_dir", tmp_path)
    monkeypatch.setattr("app.services.system_settings.gpu_available", lambda: False)
    saved = save_system_settings(
        SystemSettings(model_tier="medium", inference_device="gpu", max_duration_minutes=30),
    )
    assert saved.inference_device == "cpu"


def test_gpu_persists_when_available(tmp_path, monkeypatch):
    monkeypatch.setattr("app.services.system_settings.settings.data_dir", tmp_path)
    monkeypatch.setattr("app.services.system_settings.gpu_available", lambda: True)
    saved = save_system_settings(
        SystemSettings(model_tier="medium", inference_device="gpu", max_duration_minutes=30),
    )
    assert saved.inference_device == "gpu"


def test_load_normalizes_stale_gpu(tmp_path, monkeypatch):
    monkeypatch.setattr("app.services.system_settings.settings.data_dir", tmp_path)
    monkeypatch.setattr("app.services.system_settings.gpu_available", lambda: False)
    path = tmp_path / "system_settings.json"
    path.write_text(
        '{"model_tier": "medium", "inference_device": "gpu", "max_duration_minutes": 30}',
        encoding="utf-8",
    )
    assert load_system_settings().inference_device == "cpu"


def test_resolve_whisper_runtime_cpu(tmp_path, monkeypatch):
    monkeypatch.setattr("app.services.system_settings.settings.data_dir", tmp_path)
    monkeypatch.setattr("app.services.system_settings.settings.whisper_compute_type", "int8")
    save_system_settings(SystemSettings(inference_device="cpu", max_duration_minutes=30))
    assert resolve_whisper_runtime() == ("cpu", "int8")


def test_resolve_whisper_runtime_cuda(tmp_path, monkeypatch):
    monkeypatch.setattr("app.services.system_settings.settings.data_dir", tmp_path)
    monkeypatch.setattr("app.services.system_settings.gpu_available", lambda: True)
    monkeypatch.setattr("app.services.system_settings.detect_gpu_backend", lambda: "cuda")
    save_system_settings(SystemSettings(inference_device="gpu", max_duration_minutes=30))
    assert resolve_whisper_runtime() == ("cuda", "float16")
    assert resolve_diarization_torch_device() == "cuda"


def test_resolve_whisper_runtime_mps_keeps_whisper_on_cpu(tmp_path, monkeypatch):
    monkeypatch.setattr("app.services.system_settings.settings.data_dir", tmp_path)
    monkeypatch.setattr("app.services.system_settings.settings.whisper_compute_type", "int8")
    monkeypatch.setattr("app.services.system_settings.gpu_available", lambda: True)
    monkeypatch.setattr("app.services.system_settings.detect_gpu_backend", lambda: "mps")
    save_system_settings(SystemSettings(inference_device="gpu", max_duration_minutes=30))
    assert resolve_whisper_runtime() == ("cpu", "int8")
    assert resolve_diarization_torch_device() == "mps"
