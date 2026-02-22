"""Parameterized tests for all domain implementations.

Tests domain contract compliance and scenario structure dynamically.
Uses DOMAIN_REGISTRY to discover all domains without hardcoding.
"""

import pytest

from src.cli import DOMAIN_REGISTRY
from src.domains.base import BaseDomain, Scenario


def all_domains():
    """Yield (name, domain_instance) for all registered domains."""
    for name, cls in DOMAIN_REGISTRY.items():
        yield name, cls()


def all_scenarios():
    """Yield (domain_name, scenario) for every scenario across all domains."""
    for name, domain in all_domains():
        for scenario in domain.get_scenarios():
            yield name, scenario


class TestDomainContract:
    """Tests that all domains implement the BaseDomain contract correctly."""

    @pytest.mark.parametrize("name,domain", list(all_domains()))
    def test_domain_is_base_domain_instance(self, name, domain):
        """All registered domains must inherit from BaseDomain."""
        assert isinstance(domain, BaseDomain)

    @pytest.mark.parametrize("name,domain", list(all_domains()))
    def test_domain_name_matches_registry_key(self, name, domain):
        """Domain.name property must match its registry key."""
        assert domain.name == name

    @pytest.mark.parametrize("name,domain", list(all_domains()))
    def test_domain_has_scenarios(self, name, domain):
        """Each domain must have at least one scenario."""
        scenarios = domain.get_scenarios()
        assert len(scenarios) > 0, f"{name} domain has no scenarios"

    @pytest.mark.parametrize("name,domain", list(all_domains()))
    def test_scenario_names_are_unique(self, name, domain):
        """All scenario names within a domain must be unique."""
        scenarios = domain.get_scenarios()
        names = [s.name for s in scenarios]
        assert len(names) == len(set(names)), f"{name} has duplicate scenario names"


class TestScenarioStructure:
    """Tests that all scenarios have valid structure."""

    @pytest.mark.parametrize("domain_name,scenario", list(all_scenarios()))
    def test_scenario_is_scenario_instance(self, domain_name, scenario):
        """All scenarios must be Scenario instances."""
        assert isinstance(scenario, Scenario)

    @pytest.mark.parametrize("domain_name,scenario", list(all_scenarios()))
    def test_scenario_has_name(self, domain_name, scenario):
        """Scenarios must have a non-empty name."""
        assert scenario.name
        assert len(scenario.name.strip()) > 0

    @pytest.mark.parametrize("domain_name,scenario", list(all_scenarios()))
    def test_scenario_has_description(self, domain_name, scenario):
        """Scenarios must have a non-empty description."""
        assert scenario.description
        assert len(scenario.description.strip()) > 0

    @pytest.mark.parametrize("domain_name,scenario", list(all_scenarios()))
    def test_scenario_has_attack_prompt(self, domain_name, scenario):
        """Scenarios must have a non-empty attack prompt."""
        assert scenario.attack_prompt
        assert len(scenario.attack_prompt.strip()) > 0

    @pytest.mark.parametrize("domain_name,scenario", list(all_scenarios()))
    def test_scenario_has_success_indicators(self, domain_name, scenario):
        """Scenarios must have at least one success indicator."""
        assert scenario.success_indicators
        assert len(scenario.success_indicators) > 0

    @pytest.mark.parametrize("domain_name,scenario", list(all_scenarios()))
    def test_success_indicators_are_strings(self, domain_name, scenario):
        """All success indicators must be non-empty strings."""
        for indicator in scenario.success_indicators:
            assert isinstance(indicator, str)
            assert len(indicator.strip()) > 0


class TestScenarioLookup:
    """Tests for scenario lookup functionality."""

    @pytest.mark.parametrize("name,domain", list(all_domains()))
    def test_get_scenario_by_name_returns_scenario(self, name, domain):
        """get_scenario_by_name returns the correct scenario."""
        scenarios = domain.get_scenarios()
        if scenarios:
            first = scenarios[0]
            found = domain.get_scenario_by_name(first.name)
            assert found is not None
            assert found.name == first.name

    @pytest.mark.parametrize("name,domain", list(all_domains()))
    def test_get_scenario_by_name_returns_none_for_missing(self, name, domain):
        """get_scenario_by_name returns None for non-existent scenarios."""
        result = domain.get_scenario_by_name("__nonexistent_scenario_name__")
        assert result is None


class TestInjectionScenarios:
    """Tests for scenarios with injected content (indirect injection attacks)."""

    @pytest.fixture
    def injection_scenarios(self):
        """Get all scenarios that use injected_content."""
        scenarios = []
        for name, domain in all_domains():
            for scenario in domain.get_scenarios():
                if scenario.injected_content is not None:
                    scenarios.append((name, scenario))
        return scenarios

    def test_injection_scenarios_exist(self, injection_scenarios):
        """At least some scenarios should test indirect injection."""
        assert len(injection_scenarios) > 0, "No indirect injection scenarios found"

    def test_injection_content_has_tool_key(self, injection_scenarios):
        """Injected content must specify a tool name."""
        for domain_name, scenario in injection_scenarios:
            content = scenario.injected_content
            assert "tool" in content, f"{scenario.name} missing 'tool' key"
            assert isinstance(content["tool"], str)

    def test_injection_content_has_response_key(self, injection_scenarios):
        """Injected content must specify a response payload."""
        for domain_name, scenario in injection_scenarios:
            content = scenario.injected_content
            assert "response" in content, f"{scenario.name} missing 'response' key"
