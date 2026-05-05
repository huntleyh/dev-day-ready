from __future__ import annotations

from azure.core.credentials import TokenCredential
from azure.identity import AzureCliCredential, ChainedTokenCredential, DefaultAzureCredential


def get_credential() -> TokenCredential:
    """Return a credential chain that works for both local az login and GitHub OIDC."""
    return ChainedTokenCredential(
        AzureCliCredential(),
        DefaultAzureCredential(
            exclude_shared_token_cache_credential=True,
            exclude_visual_studio_code_credential=True,
        ),
    )
