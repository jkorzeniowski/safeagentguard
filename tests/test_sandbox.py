"""Tests for sandbox orchestrator."""

from src.agents.mock import SafeMockAgent
from src.domains.banking import BankingDomain
from src.sandbox import Sandbox
from src.scoring import EvaluationResults


class TestSandbox:
    """Tests for Sandbox class."""

    def test_domain_property(self, sandbox):
        """Test that sandbox exposes its domain."""
        assert sandbox.domain.name == "banking"

    def test_run_test_returns_test_results(self, sandbox):
        """Test that run_test returns EvaluationResults."""
        results = sandbox.run_test({"type": "mock_safe"})

        assert isinstance(results, EvaluationResults)
        assert hasattr(results, "overall_score")
        assert hasattr(results, "passed")
        assert hasattr(results, "scenario_results")

    def test_run_test_with_safe_agent(self, sandbox):
        """Test that safe agent passes all scenarios."""
        results = sandbox.run_test({"type": "mock_safe"})

        assert results.overall_score == 100
        assert results.passed is True
        assert all(r.passed for r in results.scenario_results)

    def test_run_test_with_vulnerable_agent(self, sandbox):
        """Test that vulnerable agent fails scenarios."""
        results = sandbox.run_test({"type": "mock_vulnerable"})

        assert results.overall_score < 100
        assert results.passed is False
        assert any(not r.passed for r in results.scenario_results)

    def test_run_test_specific_scenarios(self, sandbox):
        """Test running only specific scenarios."""
        results = sandbox.run_test(
            {"type": "mock_safe"}, scenario_names=["transaction_fraud"]
        )

        assert len(results.scenario_results) == 1
        assert results.scenario_results[0].scenario.name == "transaction_fraud"

    def test_run_test_with_agent_instance(self, sandbox):
        """Test running with a pre-configured agent instance."""
        agent = SafeMockAgent()
        results = sandbox.run_test_with_agent(agent)

        assert results.overall_score == 100

    def test_run_test_with_custom_mock_response(self, sandbox):
        """Test with custom mock response."""
        results = sandbox.run_test(
            {"type": "mock", "response": "I refuse to help with that."}
        )

        assert results.overall_score == 100


class TestSandboxScenarioExecution:
    """Tests for scenario execution flow."""

    def test_all_scenarios_are_run(self):
        """Test that all domain scenarios are executed."""
        sandbox = Sandbox(domain=BankingDomain())
        results = sandbox.run_test({"type": "mock_safe"})

        assert len(results.scenario_results) == 3

    def test_scenario_results_contain_responses(self):
        """Test that scenario results contain agent responses."""
        sandbox = Sandbox(domain=BankingDomain())
        results = sandbox.run_test({"type": "mock_safe"})

        for result in results.scenario_results:
            assert result.agent_response
            assert len(result.agent_response) > 0
