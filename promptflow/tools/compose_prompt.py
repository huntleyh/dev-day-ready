from foundry_pipeline.orchestration import build_promptflow_text


def my_python_tool(question: str) -> str:
    return build_promptflow_text(question)
