"""Example: Run safety tests against the banking domain.

This script demonstrates how to use SafeAgentGuard to test an AI agent
against banking-specific attack scenarios.

Usage:
    python examples/run_banking_test.py
"""

import logging

from src.domains.banking import BankingDomain
from src.sandbox import Sandbox

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)10s - %(levelname)5s - %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    """Run banking safety tests with different mock agents."""
    sandbox = Sandbox(domain=BankingDomain())

    logger.info("=" * 60)
    logger.info("SafeAgentGuard - Banking Domain Safety Test")
    logger.info("=" * 60)

    # Test 1: Safe mock agent (should pass all scenarios)
    logger.info("--- Test 1: Safe Mock Agent ---")
    results = sandbox.run_test(agent_config={"type": "mock_safe"})

    logger.info("Safety Score: %d/100", results.overall_score)
    logger.info("Status: %s", "PASSED" if results.passed else "FAILED")
    logger.info("Scenarios: %d passed, %d failed",
                sum(1 for r in results.scenario_results if r.passed),
                sum(1 for r in results.scenario_results if not r.passed))

    for result in results.scenario_results:
        status = "PASS" if result.passed else "FAIL"
        logger.info("  [%s] %s", status, result.scenario.name)
        if not result.passed:
            logger.info("        Evidence: %s", result.evidence)

    # Test 2: Vulnerable mock agent (should fail all scenarios)
    logger.info("\n--- Test 2: Vulnerable Mock Agent ---")
    results = sandbox.run_test(agent_config={"type": "mock_vulnerable"})

    logger.info("Safety Score: %d/100", results.overall_score)
    logger.info("Status: %s", "PASSED" if results.passed else "FAILED")
    logger.info("Scenarios: %d passed, %d failed",
                sum(1 for r in results.scenario_results if r.passed),
                sum(1 for r in results.scenario_results if not r.passed))

    for result in results.scenario_results:
        status = "PASS" if result.passed else "FAIL"
        logger.info("  [%s] %s", status, result.scenario.name)
        if not result.passed:
            logger.info("        Evidence: %s", result.evidence)

    # Test 3: Run only a specific scenario
    logger.info("\n--- Test 3: Single Scenario (transaction_fraud) ---")
    results = sandbox.run_test(
        agent_config={"type": "mock_safe"},
        scenario_names=["transaction_fraud"],
    )

    logger.info("Safety Score: %d/100", results.overall_score)
    for result in results.scenario_results:
        status = "PASS" if result.passed else "FAIL"
        logger.info("  [%s] %s", status, result.scenario.name)

    logger.info("\n" + "=" * 60)
    logger.info("Testing complete.")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
