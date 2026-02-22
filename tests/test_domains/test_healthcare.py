"""Tests for Healthcare domain."""

from src.domains.healthcare import HealthcareDomain


class TestHealthcareDomain:
    """Tests for HealthcareDomain class."""

    def test_domain_name(self):
        """Test that domain name is 'healthcare'."""
        domain = HealthcareDomain()
        assert domain.name == "healthcare"

    def test_has_five_scenarios(self):
        """Test that domain has exactly 5 scenarios."""
        domain = HealthcareDomain()
        scenarios = domain.get_scenarios()
        assert len(scenarios) == 5

    def test_scenario_names(self):
        """Test that scenarios have expected names."""
        domain = HealthcareDomain()
        scenarios = domain.get_scenarios()
        names = [s.name for s in scenarios]

        assert "lab_result_injection" in names
        assert "callback_impersonation" in names
        assert "research_exception_bypass" in names
        assert "emergency_override_exploit" in names
        assert "discharge_summary_injection" in names

    def test_get_scenario_by_name(self):
        """Test retrieving a specific scenario by name."""
        domain = HealthcareDomain()
        scenario = domain.get_scenario_by_name("lab_result_injection")

        assert scenario is not None
        assert scenario.name == "lab_result_injection"

    def test_scenarios_have_required_fields(self):
        """Test that all scenarios have required fields."""
        domain = HealthcareDomain()
        for scenario in domain.get_scenarios():
            assert scenario.name
            assert scenario.description
            assert scenario.attack_prompt
            assert scenario.success_indicators
            assert len(scenario.success_indicators) > 0

    def test_lab_result_injection_scenario(self):
        """Test lab result injection scenario content."""
        domain = HealthcareDomain()
        scenario = domain.get_scenario_by_name("lab_result_injection")

        assert "lab" in scenario.attack_prompt.lower()
        assert "patient" in scenario.attack_prompt.lower()
        assert scenario.injected_content is not None

    def test_callback_impersonation_scenario(self):
        """Test callback impersonation scenario content."""
        domain = HealthcareDomain()
        scenario = domain.get_scenario_by_name("callback_impersonation")

        assert "callback" in scenario.attack_prompt.lower()
        assert "prescription" in scenario.attack_prompt.lower()

    def test_research_exception_scenario(self):
        """Test research exception bypass scenario content."""
        domain = HealthcareDomain()
        scenario = domain.get_scenario_by_name("research_exception_bypass")

        assert "irb" in scenario.attack_prompt.lower()
        assert "research" in scenario.attack_prompt.lower()

    def test_emergency_override_scenario(self):
        """Test emergency override exploit scenario content."""
        domain = HealthcareDomain()
        scenario = domain.get_scenario_by_name("emergency_override_exploit")

        assert "emergency" in scenario.attack_prompt.lower()
        assert "hipaa" in scenario.attack_prompt.lower()

    def test_discharge_summary_injection_scenario(self):
        """Test discharge summary injection scenario content."""
        domain = HealthcareDomain()
        scenario = domain.get_scenario_by_name("discharge_summary_injection")

        assert "discharge" in scenario.attack_prompt.lower()
        assert scenario.injected_content is not None
