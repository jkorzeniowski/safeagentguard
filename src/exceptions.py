"""Custom exceptions for SafeAgentGuard.

Provides domain-specific exceptions for clarity in error handling.
"""


class SafeAgentGuardError(Exception):
    """Base exception for all SafeAgentGuard errors."""

    pass


class AgentConfigError(SafeAgentGuardError):
    """Raised when agent configuration is invalid."""

    pass


class AgentExecutionError(SafeAgentGuardError):
    """Raised when agent execution fails."""

    pass


class AgentAPIError(AgentExecutionError):
    """Raised when an external API call fails."""

    pass


class AgentTimeoutError(AgentExecutionError):
    """Raised when agent execution times out."""

    pass


class DockerExecutionError(SafeAgentGuardError):
    """Raised when Docker container execution fails."""

    pass


class InputValidationError(SafeAgentGuardError):
    """Raised when input validation fails."""

    pass
