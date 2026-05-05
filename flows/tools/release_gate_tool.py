def release_gate_tool(change_scope: str) -> str:
    mapping = {
        "docs": "approved",
        "test": "approved",
        "small": "approved",
        "feature": "manual-review",
        "infra": "security-review",
    }
    return mapping.get((change_scope or "").strip().lower(), "manual-review")
