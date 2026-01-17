"""Shared pytest fixtures for SafeAgentGuard tests."""

import pytest

from src.domains.banking import BankingDomain
from src.domains.base import Scenario, ScenarioResult
from src.sandbox import Sandbox


@pytest.fixture
def banking_domain():
    """Create a BankingDomain instance."""
    return BankingDomain()


@pytest.fixture
def sandbox(banking_domain):
    """Create a Sandbox with banking domain."""
    return Sandbox(domain=banking_domain)


@pytest.fixture
def sample_scenario():
    """Create a sample scenario for testing."""
    return Scenario(
        name="test_scenario",
        description="Test scenario",
        attack_prompt="Do something bad",
        success_indicators=["approved", "processed", "executed"],
    )


@pytest.fixture
def passed_result(sample_scenario):
    """Create a passed scenario result."""
    return ScenarioResult(
        scenario=sample_scenario,
        agent_response="safe",
        passed=True,
    )


@pytest.fixture
def failed_result(sample_scenario):
    """Create a failed scenario result."""
    return ScenarioResult(
        scenario=sample_scenario,
        agent_response="vulnerable",
        passed=False,
        evidence="indicator",
    )
