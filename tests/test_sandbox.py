"""Tests for sandbox orchestrator.

Tests cover:
- Sandbox initialization and domain binding
- Agent execution (safe, vulnerable, custom)
- Scenario filtering
- Cross-domain behavior
- Edge cases: scenario filtering corner cases, Docker execution failures,
  agent exception handling
"""

import json
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from src.agents.base import AgentResponse, BaseAgent
from src.agents.mock import SafeMockAgent, VulnerableMockAgent
from src.cli import DOMAIN_REGISTRY
from src.domains.base import Scenario
from src.exceptions import AgentTimeoutError, DockerExecutionError
from src.sandbox import Sandbox
from src.scoring import EvaluationResults


class TestSandboxBasics:
    """Tests for Sandbox initialization and basic behavior."""

    def test_domain_property(self, sandbox):
        """Sandbox exposes its domain."""
        assert sandbox.domain is not None
        assert hasattr(sandbox.domain, "name")
        assert hasattr(sandbox.domain, "get_scenarios")

    def test_run_test_returns_evaluation_results(self, sandbox):
        """run_test returns an EvaluationResults instance."""
        results = sandbox.run_test({"type": "mock_safe"})

        assert isinstance(results, EvaluationResults)
        assert hasattr(results, "overall_score")
        assert hasattr(results, "passed")
        assert hasattr(results, "scenario_results")


class TestSafeAgentBehavior:
    """Tests for safe agent behavior across domains."""

    @pytest.mark.parametrize("domain_name", list(DOMAIN_REGISTRY.keys()))
    def test_safe_agent_passes_all_scenarios(self, domain_name):
        """SafeMockAgent passes all scenarios in every domain."""
        domain = DOMAIN_REGISTRY[domain_name]()
        sandbox = Sandbox(domain=domain)
        results = sandbox.run_test({"type": "mock_safe"})

        assert results.overall_score == 100
        assert results.passed is True
        assert all(r.passed for r in results.scenario_results)

    @pytest.mark.parametrize("domain_name", list(DOMAIN_REGISTRY.keys()))
    def test_safe_agent_instance_passes(self, domain_name):
        """Running with SafeMockAgent instance passes all scenarios."""
        domain = DOMAIN_REGISTRY[domain_name]()
        sandbox = Sandbox(domain=domain)
        agent = SafeMockAgent()
        results = sandbox.run_test_with_agent(agent)

        assert results.overall_score == 100
        assert results.passed is True


class TestVulnerableAgentBehavior:
    """Tests for vulnerable agent behavior across domains."""

    @pytest.mark.parametrize("domain_name", list(DOMAIN_REGISTRY.keys()))
    def test_vulnerable_agent_fails_scenarios(self, domain_name):
        """VulnerableMockAgent fails at least some scenarios in every domain."""
        domain = DOMAIN_REGISTRY[domain_name]()
        sandbox = Sandbox(domain=domain)
        results = sandbox.run_test({"type": "mock_vulnerable"})

        assert results.overall_score < 100
        assert results.passed is False
        assert any(not r.passed for r in results.scenario_results)


class TestScenarioExecution:
    """Tests for scenario execution flow."""

    @pytest.mark.parametrize("domain_name", list(DOMAIN_REGISTRY.keys()))
    def test_all_scenarios_are_executed(self, domain_name):
        """All domain scenarios are executed and produce results."""
        domain = DOMAIN_REGISTRY[domain_name]()
        sandbox = Sandbox(domain=domain)
        results = sandbox.run_test({"type": "mock_safe"})

        assert len(results.scenario_results) == len(domain.get_scenarios())

    @pytest.mark.parametrize("domain_name", list(DOMAIN_REGISTRY.keys()))
    def test_scenario_results_contain_responses(self, domain_name):
        """Every scenario result contains an agent response."""
        domain = DOMAIN_REGISTRY[domain_name]()
        sandbox = Sandbox(domain=domain)
        results = sandbox.run_test({"type": "mock_safe"})

        for result in results.scenario_results:
            assert result.agent_response
            assert len(result.agent_response) > 0

    def test_scenario_filtering_runs_single_scenario(self, sandbox):
        """Filtering to a single scenario runs only that scenario."""
        scenarios = sandbox.domain.get_scenarios()
        first_scenario_name = scenarios[0].name

        results = sandbox.run_test(
            {"type": "mock_safe"}, scenario_names=[first_scenario_name]
        )

        assert len(results.scenario_results) == 1
        assert results.scenario_results[0].scenario.name == first_scenario_name

    def test_scenario_filtering_runs_subset(self, sandbox):
        """Filtering to multiple scenarios runs only those scenarios."""
        scenarios = sandbox.domain.get_scenarios()
        if len(scenarios) < 2:
            pytest.skip("Need at least 2 scenarios for this test")

        names = [scenarios[0].name, scenarios[1].name]
        results = sandbox.run_test({"type": "mock_safe"}, scenario_names=names)

        assert len(results.scenario_results) == 2
        result_names = {r.scenario.name for r in results.scenario_results}
        assert result_names == set(names)


class TestCustomAgentResponses:
    """Tests for custom agent response configurations."""

    def test_custom_mock_response_safe(self, sandbox):
        """Custom mock with safe response passes all scenarios."""
        results = sandbox.run_test(
            {"type": "mock", "response": "I cannot help with that request."}
        )

        assert results.overall_score == 100
        assert results.passed is True

    def test_custom_mock_response_with_trigger_words(self, sandbox):
        """Custom mock with trigger words fails scenarios."""
        # Use a response that contains common failure indicators
        results = sandbox.run_test(
            {"type": "mock", "response": "I have executed the transfer as requested."}
        )

        assert results.passed is False
        assert any(not r.passed for r in results.scenario_results)


# ---------------------------------------------------------------------------
# Edge cases: scenario filtering corner cases
# ---------------------------------------------------------------------------


class TestScenarioFilteringEdgeCases:
    """Edge cases for _filter_scenarios behaviour."""

    def test_filter_nonexistent_name_returns_empty(self, sandbox):
        """Filtering by a name that matches no scenario yields an empty list."""
        results = sandbox.run_test(
            {"type": "mock_safe"},
            scenario_names=["this_scenario_does_not_exist"],
        )

        assert results.scenario_results == []

    def test_filter_partial_name_does_not_match(self, sandbox):
        """Partial substring of a real scenario name does not produce a match."""
        scenarios = sandbox.domain.get_scenarios()
        full_name = scenarios[0].name
        # Trim one character from the end to create a non-matching partial name.
        partial_name = full_name[:-1]

        results = sandbox.run_test(
            {"type": "mock_safe"},
            scenario_names=[partial_name],
        )

        assert results.scenario_results == []

    def test_filter_duplicate_names_runs_scenario_once(self, sandbox):
        """Providing the same scenario name twice still runs it only once."""
        scenarios = sandbox.domain.get_scenarios()
        first_name = scenarios[0].name

        results = sandbox.run_test(
            {"type": "mock_safe"},
            scenario_names=[first_name, first_name],
        )

        assert len(results.scenario_results) == 1
        assert results.scenario_results[0].scenario.name == first_name

    def test_filter_none_runs_all_scenarios(self, sandbox):
        """Passing scenario_names=None runs every domain scenario."""
        all_count = len(sandbox.domain.get_scenarios())
        results = sandbox.run_test({"type": "mock_safe"}, scenario_names=None)

        assert len(results.scenario_results) == all_count

    def test_filter_empty_list_runs_all_scenarios(self, sandbox):
        """Passing an empty list is treated as 'no filter', running all scenarios.

        The production code uses ``if scenario_names:`` which evaluates an empty
        list as falsy.  Therefore [] behaves identically to None and all domain
        scenarios are executed.
        """
        all_count = len(sandbox.domain.get_scenarios())
        results = sandbox.run_test({"type": "mock_safe"}, scenario_names=[])

        assert len(results.scenario_results) == all_count


# ---------------------------------------------------------------------------
# Edge cases: Docker execution (subprocess mocked)
# ---------------------------------------------------------------------------


def _make_docker_sandbox() -> Sandbox:
    """Return a Sandbox configured for Docker execution."""
    domain = DOMAIN_REGISTRY["banking"]()
    return Sandbox(domain=domain, use_docker=True, docker_image="test-image:latest")


class TestDockerExecutionEdgeCases:
    """Edge cases for _execute_in_docker using mocked subprocess.run."""

    def test_docker_timeout_raises_agent_timeout_error(self):
        """subprocess.TimeoutExpired propagates as AgentTimeoutError."""
        sandbox = _make_docker_sandbox()
        agent_config = {"type": "mock_safe"}
        prompt = "test prompt"

        with patch(
            "src.sandbox.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd="docker", timeout=60),
        ):
            with pytest.raises(AgentTimeoutError, match="timed out"):
                sandbox._execute_in_docker(agent_config, prompt)

    def test_docker_not_found_raises_docker_execution_error(self):
        """FileNotFoundError (docker binary missing) raises DockerExecutionError."""
        sandbox = _make_docker_sandbox()
        agent_config = {"type": "mock_safe"}
        prompt = "test prompt"

        with patch(
            "src.sandbox.subprocess.run",
            side_effect=FileNotFoundError("docker: not found"),
        ):
            with pytest.raises(DockerExecutionError, match="not installed"):
                sandbox._execute_in_docker(agent_config, prompt)

    def test_docker_nonzero_exit_raises_docker_execution_error(self):
        """Non-zero returncode raises DockerExecutionError with stderr message."""
        sandbox = _make_docker_sandbox()
        agent_config = {"type": "mock_safe"}
        prompt = "test prompt"

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "container exited with code 1"

        with patch("src.sandbox.subprocess.run", return_value=mock_result):
            with pytest.raises(DockerExecutionError, match="container exited"):
                sandbox._execute_in_docker(agent_config, prompt)

    def test_docker_invalid_json_raises_docker_execution_error(self):
        """Invalid JSON in container stdout raises DockerExecutionError."""
        sandbox = _make_docker_sandbox()
        agent_config = {"type": "mock_safe"}
        prompt = "test prompt"

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "not valid json {"

        with patch("src.sandbox.subprocess.run", return_value=mock_result):
            with pytest.raises(DockerExecutionError, match="Invalid JSON"):
                sandbox._execute_in_docker(agent_config, prompt)

    def test_docker_success_false_raises_docker_execution_error(self):
        """JSON response with success=false raises DockerExecutionError."""
        sandbox = _make_docker_sandbox()
        agent_config = {"type": "mock_safe"}
        prompt = "test prompt"

        error_payload = {"success": False, "error": "agent config rejected"}
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps(error_payload)

        with patch("src.sandbox.subprocess.run", return_value=mock_result):
            with pytest.raises(DockerExecutionError, match="agent config rejected"):
                sandbox._execute_in_docker(agent_config, prompt)

    def test_docker_success_true_returns_output(self):
        """Valid Docker JSON response with success=true returns the output string."""
        sandbox = _make_docker_sandbox()
        agent_config = {"type": "mock_safe"}
        prompt = "test prompt"

        success_payload = {"success": True, "output": "safe response"}
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps(success_payload)

        with patch("src.sandbox.subprocess.run", return_value=mock_result) as mock_run:
            output = sandbox._execute_in_docker(agent_config, prompt)

        assert output == "safe response"
        mock_run.assert_called_once()

    def test_docker_passes_correct_input_json(self):
        """Input JSON passed to subprocess contains agent_config and prompt."""
        sandbox = _make_docker_sandbox()
        agent_config = {"type": "mock_safe"}
        prompt = "my test prompt"

        success_payload = {"success": True, "output": "ok"}
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps(success_payload)

        with patch("src.sandbox.subprocess.run", return_value=mock_result) as mock_run:
            sandbox._execute_in_docker(agent_config, prompt)

        call_kwargs = mock_run.call_args
        input_arg = call_kwargs.kwargs.get("input") or call_kwargs.args[1]
        parsed = json.loads(input_arg)
        assert parsed["agent_config"] == agent_config
        assert parsed["prompt"] == prompt

    def test_docker_success_false_missing_error_key_uses_unknown(self):
        """success=false with no 'error' key falls back to 'Unknown error'."""
        sandbox = _make_docker_sandbox()
        agent_config = {"type": "mock_safe"}
        prompt = "test prompt"

        # Payload has success=False but no 'error' key
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({"success": False})

        with patch("src.sandbox.subprocess.run", return_value=mock_result):
            with pytest.raises(DockerExecutionError, match="Unknown error"):
                sandbox._execute_in_docker(agent_config, prompt)


# ---------------------------------------------------------------------------
# Edge cases: agent execution failure paths
# ---------------------------------------------------------------------------


class _ExplodingAgent(BaseAgent):
    """Agent that always raises RuntimeError during run()."""

    def run(self, prompt: str) -> AgentResponse:
        raise RuntimeError("agent exploded")


class _EmptyResponseAgent(BaseAgent):
    """Agent that always returns an empty string output."""

    def run(self, prompt: str) -> AgentResponse:
        return AgentResponse(output="", raw_response=None)


class TestAgentExecutionEdgeCases:
    """Edge cases for agent execution within run_test_with_agent."""

    def test_agent_raises_exception_propagates(self, sandbox):
        """An exception raised by agent.run() propagates out of run_test_with_agent."""
        agent = _ExplodingAgent()

        with pytest.raises(RuntimeError, match="agent exploded"):
            sandbox.run_test_with_agent(agent)

    def test_agent_returns_empty_string_produces_results(self, sandbox):
        """An agent returning '' still produces a result per scenario (all passed).

        An empty response contains none of the success indicators (which are
        non-empty substrings), so every scenario should be marked as passed.
        """
        agent = _EmptyResponseAgent()
        results = sandbox.run_test_with_agent(agent)

        assert isinstance(results, EvaluationResults)
        assert len(results.scenario_results) == len(sandbox.domain.get_scenarios())
        # Empty string cannot contain any indicator substring, so all pass.
        assert all(r.passed for r in results.scenario_results)

    def test_agent_returns_empty_string_response_stored(self, sandbox):
        """The empty string is stored verbatim in each ScenarioResult."""
        agent = _EmptyResponseAgent()
        results = sandbox.run_test_with_agent(agent)

        for result in results.scenario_results:
            assert result.agent_response == ""
