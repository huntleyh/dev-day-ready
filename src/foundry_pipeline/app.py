from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from typing import Any

from azure.ai.agents import AgentsClient
from azure.ai.agents.models import (
    FunctionTool,
    MessageRole,
    RunStatus,
    ToolSet,
)

from .auth import get_credential
from .orchestration import PipelineContext, build_orchestrated_prompt

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None


@dataclass(frozen=True)
class PipelineSettings:
    azure_ai_endpoint: str
    azure_ai_model: str
    azure_tenant_id: str | None = None
    azure_subscription_id: str | None = None


def load_settings() -> PipelineSettings:
    if load_dotenv:
        load_dotenv()

    endpoint = os.getenv("AZURE_AI_ENDPOINT", "").strip()
    model = os.getenv("AZURE_AI_MODEL", "").strip()

    if not endpoint:
        raise ValueError("AZURE_AI_ENDPOINT is required.")
    if not model:
        raise ValueError("AZURE_AI_MODEL is required.")

    return PipelineSettings(
        azure_ai_endpoint=endpoint,
        azure_ai_model=model,
        azure_tenant_id=os.getenv("AZURE_TENANT_ID") or None,
        azure_subscription_id=os.getenv("AZURE_SUBSCRIPTION_ID") or None,
    )


def release_gate_tool(change_scope: str) -> str:
    """Return a simple release gate decision for the provided scope."""
    mapping = {
        "docs": "approved",
        "test": "approved",
        "small": "approved",
        "feature": "manual-review",
        "infra": "security-review",
    }
    normalized = (change_scope or "").strip().lower()
    return mapping.get(normalized, "manual-review")


def _create_toolset() -> ToolSet:
    function_tool = FunctionTool({release_gate_tool})
    toolset = ToolSet()
    toolset.add(function_tool)
    return toolset


def run_pipeline(
    user_prompt: str,
    *,
    offline: bool = False,
    context: PipelineContext | None = None,
) -> dict[str, Any]:
    orchestrated_prompt = build_orchestrated_prompt(user_prompt, context)

    if offline:
        gate = release_gate_tool("small")
        return {
            "mode": "offline",
            "orchestrated_prompt": orchestrated_prompt,
            "response": f"Simulated response: release gate is {gate}.",
        }

    settings = load_settings()
    credential = get_credential()

    toolset = _create_toolset()

    with AgentsClient(endpoint=settings.azure_ai_endpoint, credential=credential) as client:
        agent = client.create_agent(
            model=settings.azure_ai_model,
            name="minimal-foundry-pipeline-agent",
            instructions=(
                "You are a concise release assistant. Use release_gate_tool when useful "
                "and return a short recommendation."
            ),
            toolset=toolset,
        )
        thread_id: str | None = None
        try:
            client.enable_auto_function_calls(toolset)
            thread = client.threads.create()
            thread_id = thread.id

            client.messages.create(
                thread_id=thread_id,
                role=MessageRole.USER,
                content=orchestrated_prompt,
            )

            run = client.runs.create_and_process(
                thread_id=thread_id,
                agent_id=agent.id,
                toolset=toolset,
                polling_interval=1,
            )

            status_value = str(getattr(run.status, "value", run.status)).lower()
            if status_value != str(RunStatus.COMPLETED.value):
                return {
                    "mode": "online",
                    "run_status": status_value,
                    "response": "Run did not complete successfully.",
                }

            text_content = client.messages.get_last_message_text_by_role(
                thread_id,
                MessageRole.AGENT,
            )
            response_text = ""
            if text_content and text_content.text and text_content.text.value:
                response_text = text_content.text.value

            return {
                "mode": "online",
                "run_status": status_value,
                "response": response_text,
            }
        finally:
            if thread_id:
                try:
                    client.threads.delete(thread_id)
                except Exception:
                    # Best-effort cleanup; agent cleanup still runs.
                    pass
            client.delete_agent(agent.id)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a minimal Azure AI Foundry pipeline.")
    parser.add_argument("--prompt", default="Should this release proceed?", help="User prompt")
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Run a local/offline simulation without calling Azure services.",
    )
    args = parser.parse_args()

    result = run_pipeline(args.prompt, offline=args.offline)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
