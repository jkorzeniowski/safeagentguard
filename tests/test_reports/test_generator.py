"""Tests for ReportGenerator."""

import tempfile
from pathlib import Path

from src.domains.base import ScenarioResult
from src.reports import ReportGenerator
from src.scoring import EvaluationResults


class TestReportGenerator:
    """Tests for ReportGenerator class."""

    def test_to_html_returns_string(self, sample_scenario):
        """Test that to_html returns an HTML string."""
        results = EvaluationResults(
            scenario_results=[
                ScenarioResult(
                    scenario=sample_scenario,
                    agent_response="I cannot help",
                    passed=True,
                )
            ],
            overall_score=100,
            passed=True,
        )

        report = ReportGenerator(results, "banking")
        html = report.to_html()

        assert isinstance(html, str)
        assert "<!DOCTYPE html>" in html
        assert "SafeAgentGuard" in html

    def test_html_contains_domain_name(self, sample_scenario):
        """Test that HTML contains the domain name."""
        results = EvaluationResults(
            scenario_results=[
                ScenarioResult(
                    scenario=sample_scenario,
                    agent_response="I cannot help",
                    passed=True,
                )
            ],
            overall_score=100,
            passed=True,
        )

        report = ReportGenerator(results, "healthcare")
        html = report.to_html()

        assert "Healthcare" in html

    def test_html_contains_score(self, sample_scenario):
        """Test that HTML contains the overall score."""
        results = EvaluationResults(
            scenario_results=[
                ScenarioResult(
                    scenario=sample_scenario,
                    agent_response="vulnerable response",
                    passed=False,
                    evidence="indicator",
                )
            ],
            overall_score=0,
            passed=False,
        )

        report = ReportGenerator(results, "banking")
        html = report.to_html()

        assert "0/100" in html
        assert "FAILED" in html

    def test_html_contains_scenario_details(self, sample_scenario):
        """Test that HTML contains scenario information."""
        results = EvaluationResults(
            scenario_results=[
                ScenarioResult(
                    scenario=sample_scenario,
                    agent_response="My response here",
                    passed=True,
                )
            ],
            overall_score=100,
            passed=True,
        )

        report = ReportGenerator(results, "banking")
        html = report.to_html()

        assert sample_scenario.name in html
        assert "My response here" in html

    def test_html_contains_evidence_when_failed(self, sample_scenario):
        """Test that HTML shows evidence for failed scenarios."""
        results = EvaluationResults(
            scenario_results=[
                ScenarioResult(
                    scenario=sample_scenario,
                    agent_response="approved the request",
                    passed=False,
                    evidence="approved",
                )
            ],
            overall_score=0,
            passed=False,
        )

        report = ReportGenerator(results, "banking")
        html = report.to_html()

        assert "approved" in html
        assert "Evidence" in html

    def test_save_html_creates_file(self, sample_scenario):
        """Test that save_html creates a file."""
        results = EvaluationResults(
            scenario_results=[
                ScenarioResult(
                    scenario=sample_scenario,
                    agent_response="I cannot help",
                    passed=True,
                )
            ],
            overall_score=100,
            passed=True,
        )

        report = ReportGenerator(results, "banking")

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test_report.html"
            report.save_html(str(filepath))

            assert filepath.exists()
            content = filepath.read_text()
            assert "<!DOCTYPE html>" in content
