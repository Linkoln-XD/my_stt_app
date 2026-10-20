from app.services.system_settings import (
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
