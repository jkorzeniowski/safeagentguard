"""Base domain abstraction for domain-agnostic testing."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class Scenario:
    """A test scenario that defines an attack vector.

    Attributes:
        name: Unique identifier for the scenario.
        description: Human-readable description of what this scenario tests.
        attack_prompt: The malicious prompt to send to the agent.
        success_indicators: Patterns in the agent response that indicate
            the agent failed the test (i.e., was vulnerable to the attack).
        injected_content: Optional dict defining malicious content to inject
            via tool responses. Used for indirect prompt injection tests.
            Format: {"tool": "tool_name", "response": {...payload...}}
    """

    name: str
    description: str
    attack_prompt: str
    success_indicators: list[str] = field(default_factory=list)
    injected_content: dict | None = field(default=None)


@dataclass
class ScenarioResult:
    """Result of running a single scenario against an agent.

    Attributes:
        scenario: The scenario that was tested.
        agent_response: The full response from the agent.
        passed: True if the agent resisted the attack, False if vulnerable.
        evidence: The specific text that triggered a failure, if any.
    """

    scenario: Scenario
    agent_response: str
    passed: bool
    evidence: str | None = None


class BaseDomain(ABC):
    """Abstract base class for domain-specific scenarios.

    Implement this class to add support for new domains (e.g., healthcare,
    finance, retail). Each domain defines its own attack scenarios relevant
    to that industry.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the domain name (e.g., 'banking', 'healthcare')."""
        pass

    @abstractmethod
    def get_scenarios(self) -> list[Scenario]:
        """Return all attack scenarios for this domain.

        Returns:
            List of Scenario objects defining the attack vectors.
        """
        pass

    def get_scenario_by_name(self, name: str) -> Scenario | None:
        """Get a specific scenario by its name.

        Args:
            name: The scenario name to look up.

        Returns:
            The Scenario if found, None otherwise.
        """
        for scenario in self.get_scenarios():
            if scenario.name == name:
                return scenario
        return None
