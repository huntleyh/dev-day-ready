# Minimal Flow Artifact

This `flows/` folder is a small orchestration artifact that mirrors the managed-agent pipeline.

Flow shape:

1. `model_step` represents the Foundry model call stage.
2. `tool_step` represents the simple release-gate tool stage.

How it connects to the managed agent pipeline:

- Runtime script (`main.py` / `foundry_pipeline.app`) creates a managed agent using `azure-ai-agents`.
- The script sends an orchestration-aware prompt (GitHub -> CI/CD -> model -> tools).
- Agent tool-calling uses the same release-gate concept as the flow artifact.
- The final model response is printed and resources are cleaned up.
