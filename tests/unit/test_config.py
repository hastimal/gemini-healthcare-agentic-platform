from app.config import get_settings


def test_settings_load():
    settings = get_settings()

    assert settings.app_name == "gemini-healthcare-agentic-platform"
    assert settings.model_provider in {"gemini", "gemma"}
