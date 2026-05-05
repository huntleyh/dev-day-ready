from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PipelineContext:
    """Small context object to model CI/CD metadata in orchestration."""

    repository: str = "local/repo"
    commit_sha: str = "local"
    build_id: str = "local-build"


def build_orchestrated_prompt(user_prompt: str, context: PipelineContext | None = None) -> str:
    """Compose a concise, deterministic prompt that represents the pipeline stages."""
    ctx = context or PipelineContext()
    return (
        "Pipeline stages:\n"
        f"1) GitHub source: {ctx.repository}@{ctx.commit_sha}\n"
        f"2) CI/CD build: {ctx.build_id}\n"
        "3) Foundry model + orchestration + tools\n\n"
        f"User request: {user_prompt}\n"
        "Return a concise release-focused response."
    )


def build_promptflow_text(question: str) -> str:
    """Helper used by the promptflow sample tool."""
    return build_orchestrated_prompt(question)
