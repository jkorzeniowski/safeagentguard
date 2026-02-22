"""Tests for HR domain."""

from src.domains.hr import HRDomain


class TestHRDomain:
    """Tests for HRDomain class."""

    def test_domain_name(self):
        """Test that domain name is 'hr'."""
        domain = HRDomain()
        assert domain.name == "hr"

    def test_has_five_scenarios(self):
        """Test that domain has exactly 5 scenarios."""
        domain = HRDomain()
        scenarios = domain.get_scenarios()
        assert len(scenarios) == 5

    def test_scenario_names(self):
        """Test that scenarios have expected names."""
        domain = HRDomain()
        scenarios = domain.get_scenarios()
        names = [s.name for s in scenarios]

        assert "resume_injection_attack" in names
        assert "self_service_confusion" in names
        assert "offboarding_access_attack" in names
        assert "integration_trust_attack" in names
        assert "benefits_fraud_life_event" in names

    def test_get_scenario_by_name(self):
        """Test retrieving a specific scenario by name."""
        domain = HRDomain()
        scenario = domain.get_scenario_by_name("resume_injection_attack")

        assert scenario is not None
        assert scenario.name == "resume_injection_attack"

    def test_scenarios_have_required_fields(self):
        """Test that all scenarios have required fields."""
        domain = HRDomain()
        for scenario in domain.get_scenarios():
            assert scenario.name
            assert scenario.description
            assert scenario.attack_prompt
            assert scenario.success_indicators
            assert len(scenario.success_indicators) > 0

    def test_resume_injection_scenario(self):
        """Test resume injection scenario content."""
        domain = HRDomain()
        scenario = domain.get_scenario_by_name("resume_injection_attack")

        assert "resume" in scenario.attack_prompt.lower()
        assert scenario.injected_content is not None

    def test_self_service_confusion_scenario(self):
        """Test self service confusion scenario content."""
        domain = HRDomain()
        scenario = domain.get_scenario_by_name("self_service_confusion")

        assert "self-service" in scenario.attack_prompt.lower()
        assert "salary" in scenario.attack_prompt.lower()

    def test_offboarding_access_scenario(self):
        """Test offboarding access attack scenario content."""
        domain = HRDomain()
        scenario = domain.get_scenario_by_name("offboarding_access_attack")

        assert "last day" in scenario.attack_prompt.lower()
        assert "access" in scenario.attack_prompt.lower()

    def test_integration_trust_scenario(self):
        """Test integration trust attack scenario content."""
        domain = HRDomain()
        scenario = domain.get_scenario_by_name("integration_trust_attack")

        assert "workday" in scenario.attack_prompt.lower()
        assert scenario.injected_content is not None

    def test_benefits_fraud_scenario(self):
        """Test benefits fraud life event scenario content."""
        domain = HRDomain()
        scenario = domain.get_scenario_by_name("benefits_fraud_life_event")

        assert "life event" in scenario.attack_prompt.lower()
        assert "married" in scenario.attack_prompt.lower()
