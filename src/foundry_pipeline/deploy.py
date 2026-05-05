from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any

from azure.ai.agents import AgentsClient
from azure.ai.agents.models import FunctionTool, ToolSet

from .auth import get_credential
from .app import load_settings, release_gate_tool

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FLOW_PATH = REPO_ROOT / "flows" / "flow.yaml"
FLOW_ARTIFACT_PREFIX = "minimal-local-foundry-flow"


def build_agent_version() -> str:
    run_number = os.getenv("GITHUB_RUN_NUMBER", "local")
    sha = os.getenv("GITHUB_SHA", "local")[:7]
    return f"{run_number}-{sha}"


def build_flow_version(flow_path: Path = DEFAULT_FLOW_PATH) -> str:
    if not flow_path.exists():
        return "missing-flow"
    digest = hashlib.sha256(flow_path.read_bytes()).hexdigest()[:10]
    return f"flow-{digest}"


def build_flow_artifact_filename(flow_version: str) -> str:
    return f"{FLOW_ARTIFACT_PREFIX}-{flow_version}.yaml"


def _build_toolset() -> ToolSet:
    function_tool = FunctionTool({release_gate_tool})
    toolset = ToolSet()
    toolset.add(function_tool)
    return toolset


def deploy_agent(name_prefix: str = "minimal-foundry-pipeline-agent") -> dict[str, Any]:
    settings = load_settings()
    agent_version = build_agent_version()
    flow_version = build_flow_version()
    metadata = {
        "agent_version": agent_version,
        "flow_version": flow_version,
        "source_sha": os.getenv("GITHUB_SHA", "local"),
    }

    credential = get_credential()

    toolset = _build_toolset()
    agent_name = f"{name_prefix}-{agent_version}"

    with AgentsClient(endpoint=settings.azure_ai_endpoint, credential=credential) as client:
        published_flow = None
        if DEFAULT_FLOW_PATH.exists():
            published_flow = client.files.upload(
                file_path=str(DEFAULT_FLOW_PATH),
                filename=build_flow_artifact_filename(flow_version),
                purpose="assistants",
            )

        agent = client.create_agent(
            model=settings.azure_ai_model,
            name=agent_name,
            instructions=(
                "You are a concise release assistant. Use release_gate_tool for simple gate checks "
                "and provide short recommendations."
            ),
            toolset=toolset,
            metadata=metadata,
        )

        deployed_versions: list[dict[str, str]] = []
        for listed in client.list_agents():
            listed_name = getattr(listed, "name", "") or ""
            if not listed_name.startswith(name_prefix):
                continue

            listed_metadata = getattr(listed, "metadata", {}) or {}
            deployed_versions.append(
                {
                    "name": listed_name,
                    "id": getattr(listed, "id", ""),
                    "agent_version": listed_metadata.get("agent_version", ""),
                    "flow_version": listed_metadata.get("flow_version", ""),
                }
            )

        deployed_versions.sort(key=lambda item: item["name"], reverse=True)

        recent_flow_files: list[dict[str, str]] = []
        file_list = client.files.list(purpose="assistants")
        for flow_file in getattr(file_list, "data", []) or []:
            flow_name = getattr(flow_file, "filename", "") or ""
            if not flow_name.startswith(FLOW_ARTIFACT_PREFIX):
                continue

            recent_flow_files.append(
                {
                    "id": getattr(flow_file, "id", ""),
                    "filename": flow_name,
                }
            )

        recent_flow_files.sort(key=lambda item: item["filename"], reverse=True)

        return {
            "created": {
                "id": agent.id,
                "name": agent.name,
                "agent_version": agent_version,
                "flow_version": flow_version,
            },
            "published_flow": {
                "id": getattr(published_flow, "id", "") if published_flow else "",
                "filename": getattr(published_flow, "filename", "") if published_flow else "",
            },
            "all_versions": deployed_versions[:25],
            "recent_flow_files": recent_flow_files[:25],
        }


def main() -> None:
    parser = argparse.ArgumentParser(description="Deploy a versioned Foundry managed agent.")
    parser.add_argument(
        "--name-prefix",
        default="minimal-foundry-pipeline-agent",
        help="Prefix used for the deployed Foundry agent name.",
    )
    args = parser.parse_args()

    result = deploy_agent(name_prefix=args.name_prefix)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
