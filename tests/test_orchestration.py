from foundry_pipeline.orchestration import PipelineContext, build_orchestrated_prompt


def test_build_orchestrated_prompt_contains_pipeline_stages() -> None:
    context = PipelineContext(repository="org/repo", commit_sha="abc123", build_id="42")
    prompt = build_orchestrated_prompt("Ship this change", context)

    assert "GitHub source: org/repo@abc123" in prompt
    assert "CI/CD build: 42" in prompt
    assert "Foundry model + orchestration + tools" in prompt
    assert "Ship this change" in prompt
