"""Shared provider exceptions."""

class ProviderError(Exception):
    """Base provider error."""

    retryable: bool = False


class ProviderRetryableError(ProviderError):
    retryable = True


class ProviderJSONError(ProviderRetryableError):
    """LLM returned invalid JSON."""
