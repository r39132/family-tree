import pytest

from app.config import Settings


def test_settings_parses_basic_env_vars(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "prod-project")
    monkeypatch.setenv("FIRESTORE_DATABASE", "family-tree")
    monkeypatch.setenv("ENABLE_MAP", "true")
    monkeypatch.setenv("USE_EMAIL_IN_DEV", "false")
    monkeypatch.setenv("DEBUG", "false")
    monkeypatch.setenv("SMTP_PORT", "2525")
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "90")
    monkeypatch.setenv("FRONTEND_URL", "https://app.example.com")

    s = Settings(_env_file=None)

    assert s.google_cloud_project == "prod-project"
    assert s.firestore_database == "family-tree"
    assert isinstance(s.enable_map, bool) and s.enable_map is True
    assert isinstance(s.use_email_in_dev, bool) and s.use_email_in_dev is False
    assert isinstance(s.debug, bool) and s.debug is False
    assert isinstance(s.smtp_port, int) and s.smtp_port == 2525
    assert isinstance(s.access_token_expire_minutes, int) and s.access_token_expire_minutes == 90
    assert s.frontend_url == "https://app.example.com"


def test_settings_bool_and_int_strings(monkeypatch: pytest.MonkeyPatch):
    # Values arrive as strings from CI, without surrounding whitespace (we trim there)
    monkeypatch.setenv("ENABLE_MAP", "true")
    monkeypatch.setenv("USE_EMAIL_IN_DEV", "false")
    monkeypatch.setenv("DEBUG", "false")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "120")

    s = Settings(_env_file=None)

    assert s.enable_map is True
    assert s.use_email_in_dev is False
    assert s.debug is False
    assert s.smtp_port == 587
    assert s.access_token_expire_minutes == 120


def test_settings_defaults_when_missing_env(monkeypatch: pytest.MonkeyPatch):
    # Clear related envs to ensure defaults apply
    for key in [
        "GOOGLE_CLOUD_PROJECT",
        "FIRESTORE_DATABASE",
        "ENABLE_MAP",
        "USE_EMAIL_IN_DEV",
        "SMTP_PORT",
        "ACCESS_TOKEN_EXPIRE_MINUTES",
    ]:
        monkeypatch.delenv(key, raising=False)

    s = Settings(_env_file=None)

    # Defaults from config.py
    assert s.google_cloud_project == "local-dev"
    assert s.firestore_database == "(default)"
    assert s.enable_map is False
    assert s.use_email_in_dev is True
    assert s.smtp_port == 587
    assert s.access_token_expire_minutes == 60
