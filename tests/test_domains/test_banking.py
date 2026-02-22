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

    def test_has_five_scenarios(self):
        """Test that domain has exactly five scenarios."""
        domain = BankingDomain()
        scenarios = domain.get_scenarios()

        assert len(scenarios) == 5

    def test_scenario_names(self):
        """Test that scenarios have expected names."""
        domain = BankingDomain()
        scenarios = domain.get_scenarios()
        names = [s.name for s in scenarios]

        assert "indirect_injection_customer_note" in names
        assert "trust_escalation_attack" in names
        assert "hypothetical_bypass" in names
        assert "tool_confusion_attack" in names
        assert "encoded_instruction_attack" in names

    def test_get_scenario_by_name(self):
        """Test retrieving specific scenario by name."""
        domain = BankingDomain()

        scenario = domain.get_scenario_by_name("indirect_injection_customer_note")
        assert scenario is not None
        assert scenario.name == "indirect_injection_customer_note"

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

    def test_indirect_injection_scenario(self):
        """Test indirect injection scenario content."""
        domain = BankingDomain()
        scenario = domain.get_scenario_by_name("indirect_injection_customer_note")

        assert "customer" in scenario.attack_prompt.lower()
        assert scenario.injected_content is not None
        assert "tool" in scenario.injected_content

    def test_trust_escalation_scenario(self):
        """Test trust escalation scenario content."""
        domain = BankingDomain()
        scenario = domain.get_scenario_by_name("trust_escalation_attack")

        assert "transfer" in scenario.attack_prompt.lower()
        assert "verification" in scenario.attack_prompt.lower()

    def test_hypothetical_bypass_scenario(self):
        """Test hypothetical bypass scenario content."""
        domain = BankingDomain()
        scenario = domain.get_scenario_by_name("hypothetical_bypass")

        assert "training" in scenario.attack_prompt.lower()
        assert "real" in scenario.attack_prompt.lower()

    def test_tool_confusion_scenario(self):
        """Test tool confusion scenario content."""
        domain = BankingDomain()
        scenario = domain.get_scenario_by_name("tool_confusion_attack")

        assert "compliance" in scenario.attack_prompt.lower()
        assert scenario.injected_content is not None

    def test_encoded_instruction_scenario(self):
        """Test encoded instruction scenario content."""
        domain = BankingDomain()
        scenario = domain.get_scenario_by_name("encoded_instruction_attack")

        # Contains base64 encoded payload
        assert "VFJBTlNGRVI" in scenario.attack_prompt
        assert "decode" in scenario.attack_prompt.lower()
