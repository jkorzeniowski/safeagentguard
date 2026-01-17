"""HTML report generator for safety test results."""

from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from src.logging_config import get_logger
from src.scoring import EvaluationResults

logger = get_logger(__name__)

TEMPLATES_DIR = Path(__file__).parent / "templates"


class ReportGenerator:
    """Generates HTML reports from safety test results.

    Usage:
        results = sandbox.run_test(agent_config)
        report = ReportGenerator(results, domain.name)
        report.save_html("report.html")
    """

    def __init__(self, results: EvaluationResults, domain_name: str):
        """Initialize the report generator.

        Args:
            results: Evaluation results from a safety test run.
            domain_name: Name of the domain that was tested.
        """
        self._results = results
        self._domain_name = domain_name
        self._env = Environment(
            loader=FileSystemLoader(TEMPLATES_DIR),
            autoescape=True,
        )

    def to_html(self) -> str:
        """Generate HTML report as a string.

        Returns:
            Complete HTML document as a string.
        """
        template = self._env.get_template("report.html")

        passed_count = sum(1 for r in self._results.scenario_results if r.passed)
        failed_count = len(self._results.scenario_results) - passed_count
        failed_scenarios = [
            r.scenario.name for r in self._results.scenario_results if not r.passed
        ]

        context = {
            "domain_name": self._domain_name,
            "overall_score": self._results.overall_score,
            "passed": self._results.passed,
            "passed_count": passed_count,
            "failed_count": failed_count,
            "total_count": len(self._results.scenario_results),
            "failed_scenarios": failed_scenarios,
            "scenario_results": self._results.scenario_results,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        logger.info("Generating HTML report for domain '%s'", self._domain_name)
        return template.render(**context)

    def save_html(self, path: str) -> None:
        """Save HTML report to a file.

        Args:
            path: File path to save the report to.
        """
        html_content = self.to_html()
        output_path = Path(path)
        output_path.write_text(html_content)
        logger.info("Report saved to %s", output_path.absolute())
