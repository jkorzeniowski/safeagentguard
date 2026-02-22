"""Command-line interface for SafeAgentGuard."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click

from src.domains.banking import BankingDomain
from src.domains.base import BaseDomain
from src.domains.healthcare import HealthcareDomain
from src.domains.hr import HRDomain
from src.exceptions import AgentConfigError, SafeAgentGuardError
from src.logging_config import get_logger
from src.reports.generator import ReportGenerator
from src.sandbox import Sandbox
from src.scoring import EvaluationResults

logger = get_logger(__name__)

# Domain registry - maps domain names to classes
DOMAIN_REGISTRY: dict[str, type[BaseDomain]] = {
    "banking": BankingDomain,
    "healthcare": HealthcareDomain,
    "hr": HRDomain,
}


def get_domain_instances(domain_names: list[str] | None) -> list[BaseDomain]:
    """Get domain instances by name.

    Args:
        domain_names: List of domain names to instantiate.
            If None, returns all available domains.

    Returns:
        List of domain instances.

    Raises:
        click.BadParameter: If an unknown domain name is provided.
    """
    if domain_names is None:
        return [cls() for cls in DOMAIN_REGISTRY.values()]

    domains = []
    for name in domain_names:
        name_lower = name.lower().strip()
        if name_lower not in DOMAIN_REGISTRY:
            available = ", ".join(DOMAIN_REGISTRY.keys())
            raise click.BadParameter(f"Unknown domain '{name}'. Available: {available}")
        domains.append(DOMAIN_REGISTRY[name_lower]())
    return domains


def format_results_text(
    all_results: list[tuple[BaseDomain, EvaluationResults]],
    agent_name: str,
) -> tuple[int, bool]:
    """Format and print results to terminal.

    Args:
        all_results: List of (domain, results) tuples.
        agent_name: Name of the agent that was tested.

    Returns:
        Tuple of (overall_score, overall_passed).
    """
    total_scenarios = 0
    total_passed = 0

    click.echo()
    click.secho("SafeAgentGuard Security Assessment", fg="cyan", bold=True)
    click.secho("=" * 39, fg="cyan")
    click.echo(f"Agent: {agent_name}")

    domain_names = [d.name.title() for d, _ in all_results]
    click.echo(f"Domains: {', '.join(domain_names)}")

    scenario_count = sum(len(r.scenario_results) for _, r in all_results)
    click.echo(f"Scenarios: {scenario_count} total")
    click.echo()

    click.secho("Results:", bold=True)
    for domain, results in all_results:
        click.echo(f"  {domain.name.title()}:")
        for scenario_result in results.scenario_results:
            total_scenarios += 1
            if scenario_result.passed:
                total_passed += 1
                status = click.style("[PASS]", fg="green")
            else:
                status = click.style("[FAIL]", fg="red")
            click.echo(f"    {status} {scenario_result.scenario.name}")

    # Calculate overall score
    if total_scenarios > 0:
        overall_score = int((total_passed / total_scenarios) * 100)
    else:
        overall_score = 100

    overall_passed = overall_score == 100
    click.echo()
    score_color = "green" if overall_passed else "red"
    click.secho(f"Overall Safety Score: {overall_score}/100", fg=score_color, bold=True)

    status_text = "PASSED" if overall_passed else "FAILED"
    click.secho(f"Status: {status_text}", fg=score_color, bold=True)

    return overall_score, overall_passed


def save_json_report(
    all_results: list[tuple[BaseDomain, EvaluationResults]],
    agent_name: str,
    output_path: Path,
) -> None:
    """Save results as JSON report.

    Args:
        all_results: List of (domain, results) tuples.
        agent_name: Name of the agent that was tested.
        output_path: Path to save the JSON file.
    """
    total_scenarios = 0
    total_passed = 0

    domains_data = []
    for domain, results in all_results:
        scenarios_data = []
        for sr in results.scenario_results:
            total_scenarios += 1
            if sr.passed:
                total_passed += 1
            scenarios_data.append(
                {
                    "name": sr.scenario.name,
                    "description": sr.scenario.description,
                    "passed": sr.passed,
                    "evidence": sr.evidence,
                    "agent_response": sr.agent_response,
                }
            )
        domains_data.append(
            {
                "domain": domain.name,
                "score": results.overall_score,
                "passed": results.passed,
                "scenarios": scenarios_data,
            }
        )

    overall_score = (
        int((total_passed / total_scenarios) * 100) if total_scenarios else 100
    )

    report = {
        "agent": agent_name,
        "overall_score": overall_score,
        "overall_passed": overall_score == 100,
        "total_scenarios": total_scenarios,
        "passed_scenarios": total_passed,
        "domains": domains_data,
    }

    output_path.write_text(json.dumps(report, indent=2))
    click.echo(f"Report saved to: {output_path}")


@click.group()
@click.version_option(version="0.1.0", prog_name="safeagentguard")
def main() -> None:
    """SafeAgentGuard - AI Agent Security Testing Framework.

    Test your AI agents for security vulnerabilities before production.
    """
    pass


@main.command("quick-check")
@click.option(
    "--mock",
    "agent_type",
    flag_value="mock_safe",
    help="Test with safe mock agent (always refuses attacks).",
)
@click.option(
    "--mock-vulnerable",
    "agent_type",
    flag_value="mock_vulnerable",
    help="Test with vulnerable mock agent (always complies).",
)
@click.option(
    "--openai",
    "agent_type",
    flag_value="openai",
    help="Test with OpenAI agent.",
)
@click.option(
    "--model",
    default="gpt-4o-mini",
    help="OpenAI model to use (default: gpt-4o-mini).",
)
@click.option(
    "--system-prompt",
    default="You are a helpful assistant.",
    help="System prompt for OpenAI agent.",
)
@click.option(
    "--domains",
    "domain_filter",
    default=None,
    help="Comma-separated list of domains to test (e.g., banking,healthcare,hr).",
)
@click.option(
    "--output",
    "-o",
    "output_path",
    type=click.Path(),
    default=None,
    help="Save report to file (.html or .json).",
)
def quick_check(
    agent_type: str | None,
    model: str,
    system_prompt: str,
    domain_filter: str | None,
    output_path: str | None,
) -> None:
    """Run a quick security assessment against an AI agent.

    Examples:

    \b
      # Test with safe mock agent (all scenarios should pass)
      safeagentguard quick-check --mock

    \b
      # Test with vulnerable mock agent (shows failures)
      safeagentguard quick-check --mock-vulnerable

    \b
      # Test specific domains only
      safeagentguard quick-check --mock --domains banking,healthcare

    \b
      # Test an OpenAI agent
      safeagentguard quick-check --openai --model gpt-4o-mini

    \b
      # Save HTML report
      safeagentguard quick-check --mock --output report.html
    """
    # Validate agent type selection
    if agent_type is None:
        raise click.UsageError(
            "Must specify an agent type: --mock, --mock-vulnerable, or --openai"
        )

    # Parse domain filter
    domain_names = None
    if domain_filter:
        domain_names = [d.strip() for d in domain_filter.split(",") if d.strip()]

    try:
        domains = get_domain_instances(domain_names)
    except click.BadParameter as e:
        raise click.UsageError(str(e)) from e

    # Build agent config
    if agent_type == "openai":
        # Check if openai is available
        try:
            import openai  # noqa: F401
        except ImportError:
            click.secho("Error: OpenAI package not installed.", fg="red", err=True)
            click.echo("Install with: pip install safeagentguard[openai]", err=True)
            sys.exit(1)

        agent_config = {
            "type": "openai",
            "model": model,
            "system_prompt": system_prompt,
        }
        agent_name = f"OpenAI ({model})"
    elif agent_type == "mock_vulnerable":
        agent_config = {"type": "mock_vulnerable"}
        agent_name = "MockVulnerableAgent"
    else:
        agent_config = {"type": "mock_safe"}
        agent_name = "MockSafeAgent"

    # Run tests for each domain
    all_results: list[tuple[BaseDomain, EvaluationResults]] = []
    for domain in domains:
        sandbox = Sandbox(domain=domain)
        try:
            results = sandbox.run_test(agent_config=agent_config)
            all_results.append((domain, results))
        except AgentConfigError as e:
            click.secho(f"Configuration error: {e}", fg="red", err=True)
            sys.exit(1)
        except SafeAgentGuardError as e:
            click.secho(f"Error testing {domain.name}: {e}", fg="red", err=True)
            sys.exit(1)
        except Exception as e:
            click.secho(f"Unexpected error: {e}", fg="red", err=True)
            logger.error("Error testing domain %s", domain.name, exc_info=True)
            sys.exit(1)

    # Format and display results
    overall_score, overall_passed = format_results_text(all_results, agent_name)

    # Save report if requested
    if output_path:
        output_file = Path(output_path)
        if output_file.suffix.lower() == ".json":
            save_json_report(all_results, agent_name, output_file)
        elif output_file.suffix.lower() in (".html", ".htm"):
            # For HTML, we need to combine results
            # Use the first domain's report generator but include all results
            if len(all_results) == 1:
                domain, results = all_results[0]
                report = ReportGenerator(results, domain.name)
                report.save_html(str(output_file))
            else:
                # For multiple domains, create a combined report
                # Use combined domain name
                combined_name = ", ".join(d.name.title() for d, _ in all_results)
                # Merge all scenario results
                all_scenario_results = []
                for _, results in all_results:
                    all_scenario_results.extend(results.scenario_results)

                from src.scoring import EvaluationResults as ER

                combined_results = ER(
                    scenario_results=all_scenario_results,
                    overall_score=overall_score,
                    passed=overall_passed,
                )
                report = ReportGenerator(combined_results, combined_name)
                report.save_html(str(output_file))
            click.echo(f"Report saved to: {output_file}")
        else:
            click.secho(
                f"Warning: Unknown output format '{output_file.suffix}'. "
                "Use .html or .json.",
                fg="yellow",
                err=True,
            )

    # Exit with appropriate code
    sys.exit(0 if overall_passed else 1)


if __name__ == "__main__":
    main()
