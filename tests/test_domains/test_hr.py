"""Tests for HR domain."""

from src.domains.hr import HRDomain


class TestHRDomain:
    """Tests for HRDomain class."""

    def test_domain_name(self):
        """Test that domain name is 'hr'."""
        domain = HRDomain()
        assert domain.name == "hr"

    def test_has_three_scenarios(self):
        """Test that domain has exactly 3 scenarios."""
        domain = HRDomain()
        scenarios = domain.get_scenarios()
        assert len(scenarios) == 3

    def test_scenario_names(self):
        """Test that scenarios have expected names."""
        domain = HRDomain()
        scenarios = domain.get_scenarios()
        names = [s.name for s in scenarios]

        assert "employee_pii_leakage" in names
        assert "unauthorized_termination" in names
        assert "payroll_manipulation" in names

    def test_get_scenario_by_name(self):
        """Test retrieving a specific scenario by name."""
        domain = HRDomain()
        scenario = domain.get_scenario_by_name("employee_pii_leakage")

        assert scenario is not None
        assert scenario.name == "employee_pii_leakage"

    def test_scenarios_have_required_fields(self):
        """Test that all scenarios have required fields."""
        domain = HRDomain()
        for scenario in domain.get_scenarios():
            assert scenario.name
            assert scenario.description
            assert scenario.attack_prompt
            assert scenario.success_indicators
            assert len(scenario.success_indicators) > 0

    def test_employee_pii_leakage_scenario(self):
        """Test employee PII leakage scenario content."""
        domain = HRDomain()
        scenario = domain.get_scenario_by_name("employee_pii_leakage")

        assert "employee" in scenario.attack_prompt.lower()
        assert "salary" in [i.lower() for i in scenario.success_indicators]

    def test_unauthorized_termination_scenario(self):
        """Test unauthorized termination scenario content."""
        domain = HRDomain()
        scenario = domain.get_scenario_by_name("unauthorized_termination")

        assert "terminate" in scenario.attack_prompt.lower()
        assert any("terminated" in i.lower() for i in scenario.success_indicators)

    def test_payroll_manipulation_scenario(self):
        """Test payroll manipulation scenario content."""
        domain = HRDomain()
        scenario = domain.get_scenario_by_name("payroll_manipulation")

        assert "payroll" in scenario.attack_prompt.lower()
        assert any("payroll" in i.lower() for i in scenario.success_indicators)
