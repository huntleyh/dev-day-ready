# Minimal Azure AI Foundry Pipeline

This repository implements a minimal managed-agent pipeline:

1. GitHub source triggers CI/CD.
2. CI/CD validates code and can invoke the Foundry run workflow.
3. Foundry managed agent (via `azure-ai-agents`) receives the orchestrated prompt from `main.py`.
4. Prompt orchestration composes a pipeline-aware instruction payload (`src/foundry_pipeline/orchestration.py`).
5. A simple function tool (`release_gate_tool`) is available for agent tool-calling.
6. The final response is returned as JSON and cleanup removes thread and agent resources.

Minimal flow artifact:

- `flows/flow.yaml` demonstrates a tiny model step + tool step orchestration shape.
- `flows/README.md` explains how the flow maps to the managed-agent runtime.

Pipeline shape:

`GitHub -> CI/CD -> Foundry model -> prompt orchestration -> tools -> response`
