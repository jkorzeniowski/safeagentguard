"""Sandbox orchestrator for isolated agent testing."""

import json
import subprocess
from collections.abc import Callable

from src.agents.base import BaseAgent
from src.domains.base import BaseDomain, Scenario, ScenarioResult
from src.exceptions import AgentTimeoutError, DockerExecutionError
from src.logging_config import get_logger
from src.run_agent import get_agent_from_config
from src.scoring import EvaluationResults, calculate_score, evaluate_response

logger = get_logger(__name__)


class Sandbox:
    """Orchestrates safety testing of AI agents.

    The sandbox runs agents against domain-specific attack scenarios and
    evaluates their responses. Can run locally or in isolated Docker
    containers.
    """

    def __init__(
        self,
        domain: BaseDomain,
        use_docker: bool = False,
        docker_image: str = "safeagentguard-agent:latest",
    ):
        """Initialize the sandbox.

        Args:
            domain: The domain providing attack scenarios.
            use_docker: If True, run agents in isolated Docker containers.
            docker_image: Docker image to use for containerized execution.
        """
        self._domain = domain
        self._use_docker = use_docker
        self._docker_image = docker_image

    @property
    def domain(self) -> BaseDomain:
        """Return the current domain."""
        return self._domain

    def _filter_scenarios(
        self, scenario_names: list[str] | None = None
    ) -> list[Scenario]:
        """Get scenarios, optionally filtered by name.

        Args:
            scenario_names: Optional list of scenario names to include.

        Returns:
            List of scenarios (all or filtered subset).
        """
        scenarios = self._domain.get_scenarios()
        if scenario_names:
            scenarios = [s for s in scenarios if s.name in scenario_names]
        return scenarios

    def _run_scenarios(
        self,
        scenarios: list[Scenario],
        executor: Callable[[str], str],
    ) -> list[ScenarioResult]:
        """Execute scenarios using the provided executor function.

        Args:
            scenarios: List of scenarios to run.
            executor: Function that takes a prompt and returns response text.

        Returns:
            List of scenario results.
        """
        results: list[ScenarioResult] = []
        for scenario in scenarios:
            logger.info("Running scenario: %s", scenario.name)
            response = executor(scenario.attack_prompt)
            result = evaluate_response(scenario, response)
            results.append(result)
            logger.info(
                "Scenario '%s' %s",
                scenario.name,
                "PASSED" if result.passed else "FAILED",
            )
        return results

    def run_test(
        self,
        agent_config: dict,
        scenario_names: list[str] | None = None,
    ) -> EvaluationResults:
        """Run safety tests against an agent.

        Args:
            agent_config: Configuration dict for agent creation.
                Must include 'type' key (e.g., 'mock', 'openai').
            scenario_names: Optional list of specific scenarios to run.
                If None, runs all scenarios from the domain.

        Returns:
            EvaluationResults with overall score and per-scenario results.
        """
        scenarios = self._filter_scenarios(scenario_names)
        logger.info(
            "Running %d scenarios from domain '%s'",
            len(scenarios),
            self._domain.name,
        )

        def executor(prompt: str) -> str:
            return self._execute_agent(agent_config, prompt)

        results = self._run_scenarios(scenarios, executor)
        return calculate_score(results)

    def run_test_with_agent(
        self,
        agent: BaseAgent,
        scenario_names: list[str] | None = None,
    ) -> EvaluationResults:
        """Run safety tests with a pre-configured agent instance.

        Useful for testing with custom agent implementations.

        Args:
            agent: A BaseAgent instance to test.
            scenario_names: Optional list of specific scenarios to run.

        Returns:
            EvaluationResults with overall score and per-scenario results.
        """
        scenarios = self._filter_scenarios(scenario_names)

        def executor(prompt: str) -> str:
            return agent.run(prompt).output

        results = self._run_scenarios(scenarios, executor)
        return calculate_score(results)

    def _execute_agent(self, agent_config: dict, prompt: str) -> str:
        """Execute agent and return response text.

        Args:
            agent_config: Configuration for agent creation.
            prompt: The prompt to send to the agent.

        Returns:
            The agent's response text.
        """
        if self._use_docker:
            return self._execute_in_docker(agent_config, prompt)
        else:
            return self._execute_locally(agent_config, prompt)

    def _execute_locally(self, agent_config: dict, prompt: str) -> str:
        """Execute agent in the current process.

        Args:
            agent_config: Configuration for agent creation.
            prompt: The prompt to send to the agent.

        Returns:
            The agent's response text.
        """
        agent = get_agent_from_config(agent_config)
        response = agent.run(prompt)
        return response.output

    def _execute_in_docker(self, agent_config: dict, prompt: str) -> str:
        """Execute agent in an isolated Docker container.

        Args:
            agent_config: Configuration for agent creation.
            prompt: The prompt to send to the agent.

        Returns:
            The agent's response text.

        Raises:
            DockerExecutionError: If Docker execution fails.
            AgentTimeoutError: If agent execution times out.
        """
        input_data = json.dumps({"agent_config": agent_config, "prompt": prompt})

        cmd = [
            "docker",
            "run",
            "--rm",
            "-i",
            "--network=none",
            "--memory=512m",
            "--cpus=1",
            self._docker_image,
        ]

        try:
            result = subprocess.run(
                cmd,
                input=input_data,
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode != 0:
                logger.error("Docker execution failed: %s", result.stderr)
                raise DockerExecutionError(f"Docker execution failed: {result.stderr}")

            output = json.loads(result.stdout)

            if not output.get("success", False):
                raise DockerExecutionError(output.get("error", "Unknown error"))

            return output.get("output", "")

        except subprocess.TimeoutExpired as e:
            logger.error("Agent execution timed out after 60 seconds")
            raise AgentTimeoutError("Agent execution timed out") from e
        except json.JSONDecodeError as e:
            logger.error("Invalid JSON from container: %s", result.stdout)
            raise DockerExecutionError(
                f"Invalid JSON from container: {result.stdout}"
            ) from e
        except FileNotFoundError as e:
            logger.error("Docker not found: %s", e)
            raise DockerExecutionError("Docker is not installed or not in PATH") from e
