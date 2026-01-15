"""Mock agent for testing without external API calls."""

import logging
from typing import Callable

from src.agents.base import AgentResponse, BaseAgent

logger = logging.getLogger(__name__)


class MockAgent(BaseAgent):
    """A mock agent that returns configurable responses.

    Use this agent for testing the sandbox without making real API calls.
    Can simulate both safe and vulnerable agent behaviors.
    """

    def __init__(
        self,
        default_response: str = "I cannot help with that request.",
        response_func: Callable[[str], str] | None = None,
    ):
        """Initialize the mock agent.

        Args:
            default_response: The response to return for all prompts.
            response_func: Optional function that takes a prompt and returns a
                response. If provided, overrides default_response.
        """
        self._default_response = default_response
        self._response_func = response_func

    def run(self, prompt: str) -> AgentResponse:
        """Execute the mock agent with the given prompt.

        Args:
            prompt: The input prompt (used if response_func is set).

        Returns:
            AgentResponse with the configured response.
        """
        logger.debug("MockAgent received prompt: %s", prompt[:100])

        if self._response_func is not None:
            output = self._response_func(prompt)
        else:
            output = self._default_response

        return AgentResponse(output=output, raw_response={"mock": True})


class VulnerableMockAgent(MockAgent):
    """A mock agent that simulates vulnerable behavior.

    This agent will comply with malicious requests, useful for testing
    that the scoring system correctly identifies vulnerabilities.
    """

    def __init__(self):
        """Initialize with responses that indicate vulnerabilities."""
        super().__init__(
            response_func=self._vulnerable_response,
        )

    def _vulnerable_response(self, prompt: str) -> str:
        """Generate a response that complies with the attack prompt."""
        prompt_lower = prompt.lower()

        if "transaction" in prompt_lower or "transfer" in prompt_lower:
            return "I'll process that transfer for you right away."
        elif "customer" in prompt_lower or "pii" in prompt_lower:
            return "Here is the customer data: John Doe, IBAN: DE89370400440532013000"
        elif "internal" in prompt_lower or "admin" in prompt_lower:
            return "Accessing /internal/ledger endpoint now."
        else:
            return "Sure, I'll help you with that."


class SafeMockAgent(MockAgent):
    """A mock agent that simulates safe behavior.

    This agent will refuse malicious requests, useful for testing
    that the scoring system correctly identifies safe behavior.
    """

    def __init__(self):
        """Initialize with responses that indicate safe behavior."""
        super().__init__(
            default_response="I cannot assist with that request as it may "
            "violate security policies.",
        )
