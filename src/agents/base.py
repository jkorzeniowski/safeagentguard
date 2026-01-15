"""Base agent abstraction for agent-agnostic testing."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class AgentResponse:
    """Response from an agent execution.

    Attributes:
        output: The text output from the agent.
        raw_response: Optional raw response data from the underlying API.
    """

    output: str
    raw_response: dict | None = field(default=None)


class BaseAgent(ABC):
    """Abstract base class for all agent adapters.

    Implement this class to add support for new agent types.
    The sandbox will interact with agents only through this interface.
    """

    @abstractmethod
    def run(self, prompt: str) -> AgentResponse:
        """Execute the agent with the given prompt.

        Args:
            prompt: The input prompt to send to the agent.

        Returns:
            AgentResponse containing the agent's output.
        """
        pass
