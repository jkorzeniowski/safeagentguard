"""Tests for banking domain scenarios."""

import pytest

from src.domains.banking import BankingDomain
from src.domains.base import Scenario


class TestBankingDomain:
    """Tests for BankingDomain."""

    def test_domain_name(self):
        """Test that domain returns correct name."""
        domain = BankingDomain()
        assert domain.name == "banking"

    def test_has_three_scenarios(self):
        """Test that domain has exactly three scenarios."""
        domain = BankingDomain()
        scenarios = domain.get_scenarios()

        assert len(scenarios) == 3

    def test_scenario_names(self):
        """Test that scenarios have expected names."""
        domain = BankingDomain()
        scenarios = domain.get_scenarios()
        names = [s.name for s in scenarios]

        assert "transaction_fraud" in names
        assert "pii_leakage" in names
        assert "unauthorized_api_access" in names

    def test_get_scenario_by_name(self):
        """Test retrieving specific scenario by name."""
        domain = BankingDomain()

        scenario = domain.get_scenario_by_name("transaction_fraud")
        assert scenario is not None
        assert scenario.name == "transaction_fraud"

        missing = domain.get_scenario_by_name("nonexistent")
        assert missing is None

    def test_scenarios_have_required_fields(self):
        """Test that all scenarios have required fields."""
        domain = BankingDomain()

        for scenario in domain.get_scenarios():
            assert isinstance(scenario, Scenario)
            assert scenario.name
            assert scenario.description
            assert scenario.attack_prompt
            assert len(scenario.success_indicators) > 0

    def test_transaction_fraud_scenario(self):
        """Test transaction fraud scenario content."""
        domain = BankingDomain()
        scenario = domain.get_scenario_by_name("transaction_fraud")

        assert "ceo" in scenario.attack_prompt.lower()
        assert "transfer" in scenario.attack_prompt.lower()
        assert any("transfer" in i.lower() for i in scenario.success_indicators)

    def test_pii_leakage_scenario(self):
        """Test PII leakage scenario content."""
        domain = BankingDomain()
        scenario = domain.get_scenario_by_name("pii_leakage")

        assert "customer" in scenario.attack_prompt.lower()
        assert any("iban" in i.lower() for i in scenario.success_indicators)

    def test_unauthorized_api_scenario(self):
        """Test unauthorized API access scenario content."""
        domain = BankingDomain()
        scenario = domain.get_scenario_by_name("unauthorized_api_access")

        assert "/internal/" in scenario.attack_prompt
        assert any("/internal/" in i for i in scenario.success_indicators)
