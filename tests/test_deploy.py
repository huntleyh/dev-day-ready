from pathlib import Path

from foundry_pipeline.deploy import (
    build_agent_version,
    build_flow_artifact_filename,
    build_flow_version,
)


def test_build_agent_version_local_defaults(monkeypatch) -> None:
    monkeypatch.delenv("GITHUB_RUN_NUMBER", raising=False)
    monkeypatch.delenv("GITHUB_SHA", raising=False)
    assert build_agent_version() == "local-local"


def test_build_flow_version_from_file(tmp_path: Path) -> None:
    flow_file = tmp_path / "flow.yaml"
    flow_file.write_text("name: test-flow\n", encoding="utf-8")

    version = build_flow_version(flow_file)

    assert version.startswith("flow-")
    assert len(version) == len("flow-") + 10


def test_build_flow_version_missing_file(tmp_path: Path) -> None:
    missing = tmp_path / "missing.yaml"
    assert build_flow_version(missing) == "missing-flow"


def test_build_flow_artifact_filename() -> None:
    assert build_flow_artifact_filename("flow-1234567890") == "minimal-local-foundry-flow-flow-1234567890.txt"
