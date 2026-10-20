import pytest

from app.services.system_settings import (
    MAX_DURATION_MINUTES,
    MIN_DURATION_MINUTES,
    SystemSettings,
    get_max_duration_sec,
    load_system_settings,
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
