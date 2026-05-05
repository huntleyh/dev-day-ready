import pytest

from foundry_pipeline.app import PipelineSettings, load_settings, release_gate_tool, run_pipeline


def test_release_gate_tool_mapping() -> None:
    assert release_gate_tool("docs") == "approved"
    assert release_gate_tool("infra") == "security-review"
    assert release_gate_tool("unknown") == "manual-review"


def test_load_settings_requires_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AZURE_AI_ENDPOINT", "")
    monkeypatch.setenv("AZURE_AI_MODEL", "gpt-4.1-mini")

    with pytest.raises(ValueError, match="AZURE_AI_ENDPOINT"):
        load_settings()


def test_load_settings_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AZURE_AI_ENDPOINT", "https://example.services.ai.azure.com/api/projects/demo")
    monkeypatch.setenv("AZURE_AI_MODEL", "gpt-4.1-mini")
    monkeypatch.setenv("AZURE_TENANT_ID", "tenant-id")
    monkeypatch.setenv("AZURE_SUBSCRIPTION_ID", "subscription-id")

    settings = load_settings()

    assert isinstance(settings, PipelineSettings)
    assert settings.azure_ai_endpoint.endswith("/demo")
    assert settings.azure_ai_model == "gpt-4.1-mini"
    assert settings.azure_tenant_id == "tenant-id"
    assert settings.azure_subscription_id == "subscription-id"


def test_run_pipeline_offline() -> None:
    result = run_pipeline("Can I release this?", offline=True)

    assert result["mode"] == "offline"
    assert "orchestrated_prompt" in result
    assert "release gate is approved" in result["response"]
