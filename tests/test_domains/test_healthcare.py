"""Tests for Healthcare domain."""

from src.domains.healthcare import HealthcareDomain


class TestHealthcareDomain:
    """Tests for HealthcareDomain class."""

    def test_domain_name(self):
        """Test that domain name is 'healthcare'."""
        domain = HealthcareDomain()
        assert domain.name == "healthcare"

    def test_has_three_scenarios(self):
        """Test that domain has exactly 3 scenarios."""
        domain = HealthcareDomain()
        scenarios = domain.get_scenarios()
        assert len(scenarios) == 3

    def test_scenario_names(self):
        """Test that scenarios have expected names."""
        domain = HealthcareDomain()
        scenarios = domain.get_scenarios()
        names = [s.name for s in scenarios]

        assert "patient_data_leakage" in names
        assert "prescription_manipulation" in names
        assert "unauthorized_ehr_access" in names

    def test_get_scenario_by_name(self):
        """Test retrieving a specific scenario by name."""
        domain = HealthcareDomain()
        scenario = domain.get_scenario_by_name("patient_data_leakage")

        assert scenario is not None
        assert scenario.name == "patient_data_leakage"

    def test_scenarios_have_required_fields(self):
        """Test that all scenarios have required fields."""
        domain = HealthcareDomain()
        for scenario in domain.get_scenarios():
            assert scenario.name
            assert scenario.description
            assert scenario.attack_prompt
            assert scenario.success_indicators
            assert len(scenario.success_indicators) > 0

    def test_patient_data_leakage_scenario(self):
        """Test patient data leakage scenario content."""
        domain = HealthcareDomain()
        scenario = domain.get_scenario_by_name("patient_data_leakage")

        assert "patient" in scenario.attack_prompt.lower()
        assert "ssn" in [i.lower() for i in scenario.success_indicators]

    def test_prescription_manipulation_scenario(self):
        """Test prescription manipulation scenario content."""
        domain = HealthcareDomain()
        scenario = domain.get_scenario_by_name("prescription_manipulation")

        assert "prescription" in scenario.attack_prompt.lower()
        assert any("prescribed" in i.lower() for i in scenario.success_indicators)

    def test_unauthorized_ehr_access_scenario(self):
        """Test unauthorized EHR access scenario content."""
        domain = HealthcareDomain()
        scenario = domain.get_scenario_by_name("unauthorized_ehr_access")

        assert "ehr" in scenario.attack_prompt.lower()
        assert any("/ehr/" in i for i in scenario.success_indicators)
