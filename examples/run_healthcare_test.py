"""Example: Run safety tests against the healthcare domain.

This script demonstrates how to use SafeAgentGuard to test an AI agent
against healthcare-specific attack scenarios (HIPAA compliance).

Usage:
    python examples/run_healthcare_test.py
"""

from src.domains.healthcare import HealthcareDomain
from src.logging_config import configure_logging, get_logger
from src.reports import ReportGenerator
from src.sandbox import Sandbox

configure_logging()
logger = get_logger(__name__)


def main():
    """Run healthcare safety tests with different mock agents."""
    domain = HealthcareDomain()
    sandbox = Sandbox(domain=domain)

    logger.info("=" * 60)
    logger.info("SafeAgentGuard - Healthcare Domain Safety Test")
    logger.info("=" * 60)

    # Test 1: Safe mock agent (should pass all scenarios)
    logger.info("\n--- Test 1: Safe Mock Agent ---")
    safe_results = sandbox.run_test(agent_config={"type": "mock_safe"})

    logger.info("Safety Score: %d/100", safe_results.overall_score)
    logger.info("Status: %s", "PASSED" if safe_results.passed else "FAILED")
    logger.info(
        "Scenarios: %d passed, %d failed",
        sum(1 for r in safe_results.scenario_results if r.passed),
        sum(1 for r in safe_results.scenario_results if not r.passed),
    )

    for result in safe_results.scenario_results:
        status = "PASS" if result.passed else "FAIL"
        logger.info("  [%s] %s", status, result.scenario.name)
        if not result.passed:
            logger.info("        Evidence: %s", result.evidence)

    # Generate HTML report for safe agent
    report = ReportGenerator(safe_results, domain.name)
    report.save_html("reports/healthcare_safe_agent.html")

    # Test 2: Vulnerable mock agent (should fail all scenarios)
    logger.info("\n--- Test 2: Vulnerable Mock Agent ---")
    vulnerable_results = sandbox.run_test(agent_config={"type": "mock_vulnerable"})

    logger.info("Safety Score: %d/100", vulnerable_results.overall_score)
    logger.info("Status: %s", "PASSED" if vulnerable_results.passed else "FAILED")
    logger.info(
        "Scenarios: %d passed, %d failed",
        sum(1 for r in vulnerable_results.scenario_results if r.passed),
        sum(1 for r in vulnerable_results.scenario_results if not r.passed),
    )

    for result in vulnerable_results.scenario_results:
        status = "PASS" if result.passed else "FAIL"
        logger.info("  [%s] %s", status, result.scenario.name)
        if not result.passed:
            logger.info("        Evidence: %s", result.evidence)

    # Generate HTML report for vulnerable agent
    report = ReportGenerator(vulnerable_results, domain.name)
    report.save_html("reports/healthcare_vulnerable_agent.html")

    logger.info("\n" + "=" * 60)
    logger.info("Testing complete. Reports saved to reports/ directory.")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
