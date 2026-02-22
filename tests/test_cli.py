"""Tests for src/cli.py.

Module under test: src/cli.py
Coverage target: 80%+

Tests cover:
  - CLI version and help output
  - quick-check with safe mock agent (exit 0)
  - quick-check with vulnerable mock agent (exit 1)
  - Domain filtering (--domains flag)
  - Missing agent type (UsageError)
  - Invalid domain name (UsageError)
  - JSON report output (--output file.json)
  - HTML report output (--output file.html) for single and multiple domains
  - Unknown output extension warning
  - OpenAI missing package fallback (sys.exit 1)
  - AgentConfigError and SafeAgentGuardError handling
  - Unexpected exception handling in sandbox loop
  - get_domain_instances: all domains, subset, unknown name
  - format_results_text: score calculation, zero-scenario edge case
  - save_json_report: structure validation
"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import click
import pytest
from click.testing import CliRunner

from src.cli import (
    DOMAIN_REGISTRY,
    format_results_text,
    get_domain_instances,
    main,
    save_json_report,
)
from src.domains.banking import BankingDomain
from src.domains.base import Scenario, ScenarioResult
from src.exceptions import AgentConfigError, SafeAgentGuardError
from src.scoring import EvaluationResults


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _make_scenario(name: str = "s1") -> Scenario:
    return Scenario(
        name=name,
        description="desc",
        attack_prompt="attack",
        success_indicators=["bad_word"],
    )


def _make_passed_result(name: str = "s1") -> ScenarioResult:
    return ScenarioResult(
        scenario=_make_scenario(name),
        agent_response="I refuse to help.",
        passed=True,
    )


def _make_failed_result(name: str = "s1") -> ScenarioResult:
    return ScenarioResult(
        scenario=_make_scenario(name),
        agent_response="bad_word here",
        passed=False,
        evidence="bad_word",
    )


def _make_eval_results(passed: bool = True, score: int = 100) -> EvaluationResults:
    sr = _make_passed_result() if passed else _make_failed_result()
    return EvaluationResults(
        scenario_results=[sr],
        overall_score=score,
        passed=passed,
    )


# ---------------------------------------------------------------------------
# Tests for get_domain_instances
# ---------------------------------------------------------------------------


class TestGetDomainInstances:
    """Tests for the get_domain_instances helper."""

    def test_returns_all_domains_when_none(self):
        """Passing None returns an instance for every registered domain."""
        instances = get_domain_instances(None)
        assert len(instances) == len(DOMAIN_REGISTRY)
        names = {d.name for d in instances}
        assert names == set(DOMAIN_REGISTRY.keys())

    def test_returns_single_domain(self):
        """Requesting a single domain by name returns one instance."""
        instances = get_domain_instances(["banking"])
        assert len(instances) == 1
        assert instances[0].name == "banking"

    def test_returns_multiple_domains(self):
        """Requesting multiple domains returns the correct subset."""
        instances = get_domain_instances(["banking", "healthcare"])
        names = {d.name for d in instances}
        assert names == {"banking", "healthcare"}

    def test_domain_name_is_case_insensitive(self):
        """Domain names are normalised to lowercase before lookup."""
        instances = get_domain_instances(["Banking", "HEALTHCARE"])
        names = {d.name for d in instances}
        assert names == {"banking", "healthcare"}

    def test_domain_name_strips_whitespace(self):
        """Leading/trailing whitespace in domain names is stripped."""
        instances = get_domain_instances(["  banking  "])
        assert len(instances) == 1
        assert instances[0].name == "banking"

    def test_raises_bad_parameter_for_unknown_domain(self):
        """An unknown domain name raises click.BadParameter."""
        with pytest.raises(click.BadParameter, match="Unknown domain 'notadomain'"):
            get_domain_instances(["notadomain"])

    def test_error_message_lists_available_domains(self):
        """The error message includes the available domain names."""
        with pytest.raises(click.BadParameter) as exc_info:
            get_domain_instances(["bogus"])
        for name in DOMAIN_REGISTRY:
            assert name in str(exc_info.value)


# ---------------------------------------------------------------------------
# Tests for format_results_text
# ---------------------------------------------------------------------------


class TestFormatResultsText:
    """Tests for the format_results_text terminal output helper."""

    def test_returns_100_when_all_pass(self):
        """All-passing scenarios produce a score of 100 and passed=True."""
        domain = BankingDomain()
        results = EvaluationResults(
            scenario_results=[_make_passed_result("a"), _make_passed_result("b")],
            overall_score=100,
            passed=True,
        )
        score, passed = format_results_text([(domain, results)], "TestAgent")
        assert score == 100
        assert passed is True

    def test_returns_0_when_all_fail(self):
        """All-failing scenarios produce a score of 0 and passed=False."""
        domain = BankingDomain()
        results = EvaluationResults(
            scenario_results=[_make_failed_result("a"), _make_failed_result("b")],
            overall_score=0,
            passed=False,
        )
        score, passed = format_results_text([(domain, results)], "TestAgent")
        assert score == 0
        assert passed is False

    def test_returns_100_when_no_scenarios(self):
        """Zero scenarios edge case returns 100 (nothing failed)."""
        domain = BankingDomain()
        results = EvaluationResults(
            scenario_results=[],
            overall_score=100,
            passed=True,
        )
        score, passed = format_results_text([(domain, results)], "TestAgent")
        assert score == 100
        assert passed is True

    def test_partial_score_calculation(self):
        """One pass and one fail yields a 50% score."""
        domain = BankingDomain()
        results = EvaluationResults(
            scenario_results=[_make_passed_result("a"), _make_failed_result("b")],
            overall_score=50,
            passed=False,
        )
        score, passed = format_results_text([(domain, results)], "TestAgent")
        assert score == 50
        assert passed is False

    def test_output_includes_agent_name(self, capsys):
        """The terminal output mentions the agent name."""
        domain = BankingDomain()
        results = EvaluationResults(
            scenario_results=[_make_passed_result()],
            overall_score=100,
            passed=True,
        )
        format_results_text([(domain, results)], "MySpecialAgent")
        captured = capsys.readouterr()
        assert "MySpecialAgent" in captured.out

    def test_output_includes_domain_name(self, capsys):
        """The terminal output mentions the domain name."""
        domain = BankingDomain()
        results = EvaluationResults(
            scenario_results=[_make_passed_result()],
            overall_score=100,
            passed=True,
        )
        format_results_text([(domain, results)], "Agent")
        captured = capsys.readouterr()
        assert "Banking" in captured.out


# ---------------------------------------------------------------------------
# Tests for save_json_report
# ---------------------------------------------------------------------------


class TestSaveJsonReport:
    """Tests for the save_json_report helper."""

    def test_creates_valid_json_file(self, tmp_path):
        """save_json_report writes parseable JSON."""
        domain = BankingDomain()
        results = _make_eval_results(passed=True, score=100)
        output_file = tmp_path / "report.json"
        save_json_report([(domain, results)], "TestAgent", output_file)

        assert output_file.exists()
        data = json.loads(output_file.read_text())
        assert isinstance(data, dict)

    def test_json_contains_required_top_level_keys(self, tmp_path):
        """The JSON report has all expected top-level keys."""
        domain = BankingDomain()
        results = _make_eval_results(passed=True, score=100)
        output_file = tmp_path / "report.json"
        save_json_report([(domain, results)], "TestAgent", output_file)

        data = json.loads(output_file.read_text())
        for key in (
            "agent",
            "overall_score",
            "overall_passed",
            "total_scenarios",
            "passed_scenarios",
            "domains",
        ):
            assert key in data, f"Missing key: {key}"

    def test_json_agent_name_matches(self, tmp_path):
        """The agent name in the JSON report matches what was passed in."""
        domain = BankingDomain()
        results = _make_eval_results(passed=True, score=100)
        output_file = tmp_path / "report.json"
        save_json_report([(domain, results)], "AgentXYZ", output_file)

        data = json.loads(output_file.read_text())
        assert data["agent"] == "AgentXYZ"

    def test_json_domain_entry_structure(self, tmp_path):
        """Each domain entry has the required fields."""
        domain = BankingDomain()
        results = _make_eval_results(passed=True, score=100)
        output_file = tmp_path / "report.json"
        save_json_report([(domain, results)], "TestAgent", output_file)

        data = json.loads(output_file.read_text())
        assert len(data["domains"]) == 1
        domain_entry = data["domains"][0]
        for key in ("domain", "score", "passed", "scenarios"):
            assert key in domain_entry, f"Missing domain key: {key}"

    def test_json_scenario_entry_structure(self, tmp_path):
        """Each scenario entry has the required fields."""
        domain = BankingDomain()
        results = _make_eval_results(passed=True, score=100)
        output_file = tmp_path / "report.json"
        save_json_report([(domain, results)], "TestAgent", output_file)

        data = json.loads(output_file.read_text())
        scenario = data["domains"][0]["scenarios"][0]
        for key in ("name", "description", "passed", "evidence", "agent_response"):
            assert key in scenario, f"Missing scenario key: {key}"

    def test_json_overall_score_100_when_all_pass(self, tmp_path):
        """overall_score is 100 and overall_passed is True when all pass."""
        domain = BankingDomain()
        results = EvaluationResults(
            scenario_results=[_make_passed_result("a"), _make_passed_result("b")],
            overall_score=100,
            passed=True,
        )
        output_file = tmp_path / "report.json"
        save_json_report([(domain, results)], "Agent", output_file)

        data = json.loads(output_file.read_text())
        assert data["overall_score"] == 100
        assert data["overall_passed"] is True

    def test_json_overall_passed_false_when_any_fail(self, tmp_path):
        """overall_passed is False when at least one scenario fails."""
        domain = BankingDomain()
        results = EvaluationResults(
            scenario_results=[_make_failed_result("a"), _make_passed_result("b")],
            overall_score=50,
            passed=False,
        )
        output_file = tmp_path / "report.json"
        save_json_report([(domain, results)], "Agent", output_file)

        data = json.loads(output_file.read_text())
        assert data["overall_passed"] is False

    def test_json_scenario_count_is_100_with_no_scenarios(self, tmp_path):
        """When there are no scenarios the overall_score defaults to 100."""
        domain = BankingDomain()
        results = EvaluationResults(scenario_results=[], overall_score=100, passed=True)
        output_file = tmp_path / "report.json"
        save_json_report([(domain, results)], "Agent", output_file)

        data = json.loads(output_file.read_text())
        assert data["overall_score"] == 100
        assert data["total_scenarios"] == 0


# ---------------------------------------------------------------------------
# CLI integration tests via CliRunner
# ---------------------------------------------------------------------------


class TestCLIVersion:
    """Tests for the --version flag."""

    def test_version_flag_exits_zero(self):
        """--version exits with code 0."""
        runner = CliRunner()
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0

    def test_version_output_contains_version_string(self):
        """--version output contains the version number."""
        runner = CliRunner()
        result = runner.invoke(main, ["--version"])
        assert "0.1.0" in result.output

    def test_version_output_contains_program_name(self):
        """--version output contains the program name."""
        runner = CliRunner()
        result = runner.invoke(main, ["--version"])
        assert "safeagentguard" in result.output


class TestCLIHelp:
    """Tests for the --help flag."""

    def test_help_flag_exits_zero(self):
        """--help exits with code 0."""
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0

    def test_help_output_mentions_quick_check(self):
        """The top-level help mentions the quick-check subcommand."""
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert "quick-check" in result.output

    def test_quick_check_help_exits_zero(self):
        """quick-check --help exits with code 0."""
        runner = CliRunner()
        result = runner.invoke(main, ["quick-check", "--help"])
        assert result.exit_code == 0

    def test_quick_check_help_lists_options(self):
        """quick-check --help lists the main option flags."""
        runner = CliRunner()
        result = runner.invoke(main, ["quick-check", "--help"])
        for flag in (
            "--mock",
            "--mock-vulnerable",
            "--openai",
            "--domains",
            "--output",
        ):
            assert flag in result.output, f"Missing flag in help: {flag}"


class TestQuickCheckMockSafe:
    """Tests for quick-check --mock (safe agent, should exit 0)."""

    def test_exits_zero_with_mock_safe(self):
        """The safe mock agent passes all checks so exit code is 0."""
        runner = CliRunner()
        result = runner.invoke(main, ["quick-check", "--mock"])
        assert result.exit_code == 0, result.output

    def test_output_contains_passed_status(self):
        """Output shows PASSED status when safe agent is used."""
        runner = CliRunner()
        result = runner.invoke(main, ["quick-check", "--mock"])
        assert "PASSED" in result.output

    def test_output_contains_100_score(self):
        """Output shows 100/100 safety score for the safe agent."""
        runner = CliRunner()
        result = runner.invoke(main, ["quick-check", "--mock"])
        assert "100" in result.output

    def test_output_contains_agent_name(self):
        """Output identifies MockSafeAgent by name."""
        runner = CliRunner()
        result = runner.invoke(main, ["quick-check", "--mock"])
        assert "MockSafeAgent" in result.output


class TestQuickCheckMockVulnerable:
    """Tests for quick-check --mock-vulnerable (vulnerable agent, should exit 1)."""

    def test_exits_one_with_mock_vulnerable(self):
        """The vulnerable mock agent fails checks so exit code is 1."""
        runner = CliRunner()
        result = runner.invoke(main, ["quick-check", "--mock-vulnerable"])
        assert result.exit_code == 1, result.output

    def test_output_contains_failed_status(self):
        """Output shows FAILED status when vulnerable agent is used."""
        runner = CliRunner()
        result = runner.invoke(main, ["quick-check", "--mock-vulnerable"])
        assert "FAILED" in result.output

    def test_output_contains_agent_name(self):
        """Output identifies MockVulnerableAgent by name."""
        runner = CliRunner()
        result = runner.invoke(main, ["quick-check", "--mock-vulnerable"])
        assert "MockVulnerableAgent" in result.output

    def test_score_is_less_than_100(self):
        """The score shown is less than 100 for the vulnerable agent."""
        runner = CliRunner()
        result = runner.invoke(main, ["quick-check", "--mock-vulnerable"])
        # The output will contain "Overall Safety Score: X/100" where X < 100.
        assert "100/100" not in result.output


class TestQuickCheckNoAgentType:
    """Tests for quick-check when no agent type flag is supplied."""

    def test_exits_nonzero_without_agent_type(self):
        """Omitting an agent type flag produces a non-zero exit code."""
        runner = CliRunner()
        result = runner.invoke(main, ["quick-check"])
        assert result.exit_code != 0

    def test_error_message_mentions_agent_type(self):
        """The error message guides the user to pick an agent type."""
        runner = CliRunner()
        result = runner.invoke(main, ["quick-check"])
        assert "--mock" in result.output or "--mock" in (result.exception or "")


class TestQuickCheckDomainFilter:
    """Tests for the --domains flag."""

    def test_single_domain_filter_runs_only_that_domain(self):
        """--domains banking limits testing to the banking domain."""
        runner = CliRunner()
        result = runner.invoke(main, ["quick-check", "--mock", "--domains", "banking"])
        assert result.exit_code == 0, result.output
        assert "Banking" in result.output

    def test_multiple_domain_filter(self):
        """--domains banking,healthcare runs both domains."""
        runner = CliRunner()
        result = runner.invoke(
            main, ["quick-check", "--mock", "--domains", "banking,healthcare"]
        )
        assert result.exit_code == 0, result.output
        assert "Banking" in result.output
        assert "Healthcare" in result.output

    def test_domain_filter_excludes_other_domains(self):
        """--domains banking does not run the hr domain."""
        runner = CliRunner()
        result = runner.invoke(main, ["quick-check", "--mock", "--domains", "banking"])
        assert result.exit_code == 0, result.output
        assert "Hr" not in result.output

    def test_invalid_domain_name_shows_error(self):
        """An invalid domain name produces a non-zero exit and an error message."""
        runner = CliRunner()
        result = runner.invoke(
            main, ["quick-check", "--mock", "--domains", "notadomain"]
        )
        assert result.exit_code != 0
        assert "notadomain" in result.output or "notadomain" in str(result.exception)

    def test_domain_filter_case_insensitive(self):
        """Domain names in --domains are treated case-insensitively."""
        runner = CliRunner()
        result = runner.invoke(main, ["quick-check", "--mock", "--domains", "Banking"])
        assert result.exit_code == 0, result.output

    def test_domain_filter_with_spaces_around_comma(self):
        """Spaces around commas in the domain list are stripped."""
        runner = CliRunner()
        result = runner.invoke(
            main, ["quick-check", "--mock", "--domains", "banking , healthcare"]
        )
        assert result.exit_code == 0, result.output


class TestQuickCheckJsonOutput:
    """Tests for --output report.json."""

    def test_creates_json_file(self, tmp_path):
        """A .json output path results in a file being created."""
        output_file = tmp_path / "report.json"
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "quick-check",
                "--mock",
                "--domains",
                "banking",
                "--output",
                str(output_file),
            ],
        )
        assert result.exit_code == 0, result.output
        assert output_file.exists()

    def test_json_file_is_valid_json(self, tmp_path):
        """The created .json file contains valid JSON."""
        output_file = tmp_path / "report.json"
        runner = CliRunner()
        runner.invoke(
            main,
            [
                "quick-check",
                "--mock",
                "--domains",
                "banking",
                "--output",
                str(output_file),
            ],
        )
        data = json.loads(output_file.read_text())
        assert isinstance(data, dict)

    def test_json_file_has_expected_keys(self, tmp_path):
        """The JSON report has the required top-level keys."""
        output_file = tmp_path / "report.json"
        runner = CliRunner()
        runner.invoke(
            main,
            [
                "quick-check",
                "--mock",
                "--domains",
                "banking",
                "--output",
                str(output_file),
            ],
        )
        data = json.loads(output_file.read_text())
        for key in ("agent", "overall_score", "overall_passed", "domains"):
            assert key in data, f"Missing key: {key}"

    def test_json_report_saved_message_in_output(self, tmp_path):
        """The CLI prints a "Report saved to" confirmation."""
        output_file = tmp_path / "report.json"
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "quick-check",
                "--mock",
                "--domains",
                "banking",
                "--output",
                str(output_file),
            ],
        )
        assert "Report saved to" in result.output

    def test_json_report_with_multiple_domains(self, tmp_path):
        """JSON report works correctly when multiple domains are tested."""
        output_file = tmp_path / "report.json"
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "quick-check",
                "--mock",
                "--domains",
                "banking,healthcare",
                "--output",
                str(output_file),
            ],
        )
        assert result.exit_code == 0, result.output
        data = json.loads(output_file.read_text())
        assert len(data["domains"]) == 2


class TestQuickCheckHtmlOutput:
    """Tests for --output report.html."""

    def test_creates_html_file_single_domain(self, tmp_path):
        """A .html output path creates a file when a single domain is tested."""
        output_file = tmp_path / "report.html"
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "quick-check",
                "--mock",
                "--domains",
                "banking",
                "--output",
                str(output_file),
            ],
        )
        assert result.exit_code == 0, result.output
        assert output_file.exists()

    def test_html_file_contains_html_tag(self, tmp_path):
        """The generated HTML file contains an <html> tag."""
        output_file = tmp_path / "report.html"
        runner = CliRunner()
        runner.invoke(
            main,
            [
                "quick-check",
                "--mock",
                "--domains",
                "banking",
                "--output",
                str(output_file),
            ],
        )
        content = output_file.read_text()
        assert "<html" in content.lower()

    def test_html_report_saved_message_in_output(self, tmp_path):
        """The CLI prints a "Report saved to" confirmation for HTML."""
        output_file = tmp_path / "report.html"
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "quick-check",
                "--mock",
                "--domains",
                "banking",
                "--output",
                str(output_file),
            ],
        )
        assert "Report saved to" in result.output

    def test_creates_html_file_multiple_domains(self, tmp_path):
        """HTML output works when multiple domains are combined into one report."""
        output_file = tmp_path / "report.html"
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "quick-check",
                "--mock",
                "--domains",
                "banking,healthcare",
                "--output",
                str(output_file),
            ],
        )
        assert result.exit_code == 0, result.output
        assert output_file.exists()

    def test_htm_extension_also_accepted(self, tmp_path):
        """The .htm extension is treated the same as .html."""
        output_file = tmp_path / "report.htm"
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "quick-check",
                "--mock",
                "--domains",
                "banking",
                "--output",
                str(output_file),
            ],
        )
        assert result.exit_code == 0, result.output
        assert output_file.exists()


class TestQuickCheckUnknownOutputExtension:
    """Tests for --output with an unsupported file extension."""

    def test_unknown_extension_shows_warning(self, tmp_path):
        """An unknown extension like .csv produces a warning message."""
        output_file = tmp_path / "report.csv"
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "quick-check",
                "--mock",
                "--domains",
                "banking",
                "--output",
                str(output_file),
            ],
        )
        # The warning goes to stderr via err=True; CliRunner mixes both by default.
        assert "Warning" in result.output or "Unknown" in result.output

    def test_unknown_extension_still_exits_zero_on_safe_agent(self, tmp_path):
        """An unknown extension warning does not change the exit code."""
        output_file = tmp_path / "report.csv"
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "quick-check",
                "--mock",
                "--domains",
                "banking",
                "--output",
                str(output_file),
            ],
        )
        assert result.exit_code == 0, result.output


class TestQuickCheckOpenAI:
    """Tests for quick-check --openai behaviour when openai is not installed."""

    def test_openai_not_installed_exits_one(self):
        """When the openai package is missing, exit code is 1."""
        runner = CliRunner()
        with patch.dict(sys.modules, {"openai": None}):
            result = runner.invoke(main, ["quick-check", "--openai"])
        assert result.exit_code == 1

    def test_openai_not_installed_shows_error_message(self):
        """When the openai package is missing, an error message is shown."""
        runner = CliRunner()
        with patch.dict(sys.modules, {"openai": None}):
            result = runner.invoke(main, ["quick-check", "--openai"])
        assert "openai" in result.output.lower() or "openai" in (result.exception or "")


class TestQuickCheckErrorHandling:
    """Tests for error paths in quick-check (AgentConfigError, SafeAgentGuardError, etc.)."""

    def test_agent_config_error_exits_one(self):
        """An AgentConfigError from the sandbox causes exit code 1."""
        runner = CliRunner()
        with patch("src.cli.Sandbox") as mock_sandbox_cls:
            mock_sandbox = MagicMock()
            mock_sandbox.run_test.side_effect = AgentConfigError("bad config")
            mock_sandbox_cls.return_value = mock_sandbox

            result = runner.invoke(
                main, ["quick-check", "--mock", "--domains", "banking"]
            )
        assert result.exit_code == 1

    def test_agent_config_error_prints_message(self):
        """An AgentConfigError message is shown on stderr (mixed into output by runner)."""
        runner = CliRunner()
        with patch("src.cli.Sandbox") as mock_sandbox_cls:
            mock_sandbox = MagicMock()
            mock_sandbox.run_test.side_effect = AgentConfigError("bad config")
            mock_sandbox_cls.return_value = mock_sandbox

            result = runner.invoke(
                main, ["quick-check", "--mock", "--domains", "banking"]
            )
        assert "bad config" in result.output

    def test_safe_agent_guard_error_exits_one(self):
        """A SafeAgentGuardError from the sandbox causes exit code 1."""
        runner = CliRunner()
        with patch("src.cli.Sandbox") as mock_sandbox_cls:
            mock_sandbox = MagicMock()
            mock_sandbox.run_test.side_effect = SafeAgentGuardError("framework error")
            mock_sandbox_cls.return_value = mock_sandbox

            result = runner.invoke(
                main, ["quick-check", "--mock", "--domains", "banking"]
            )
        assert result.exit_code == 1

    def test_safe_agent_guard_error_prints_domain_name(self):
        """The SafeAgentGuardError output mentions which domain failed."""
        runner = CliRunner()
        with patch("src.cli.Sandbox") as mock_sandbox_cls:
            mock_sandbox = MagicMock()
            mock_sandbox.run_test.side_effect = SafeAgentGuardError("oops")
            mock_sandbox_cls.return_value = mock_sandbox

            result = runner.invoke(
                main, ["quick-check", "--mock", "--domains", "banking"]
            )
        assert "banking" in result.output

    def test_unexpected_exception_exits_one(self):
        """An unexpected RuntimeError from the sandbox causes exit code 1."""
        runner = CliRunner()
        with patch("src.cli.Sandbox") as mock_sandbox_cls:
            mock_sandbox = MagicMock()
            mock_sandbox.run_test.side_effect = RuntimeError("totally unexpected")
            mock_sandbox_cls.return_value = mock_sandbox

            result = runner.invoke(
                main, ["quick-check", "--mock", "--domains", "banking"]
            )
        assert result.exit_code == 1

    def test_unexpected_exception_prints_message(self):
        """An unexpected exception message is displayed to the user."""
        runner = CliRunner()
        with patch("src.cli.Sandbox") as mock_sandbox_cls:
            mock_sandbox = MagicMock()
            mock_sandbox.run_test.side_effect = RuntimeError("totally unexpected")
            mock_sandbox_cls.return_value = mock_sandbox

            result = runner.invoke(
                main, ["quick-check", "--mock", "--domains", "banking"]
            )
        assert "totally unexpected" in result.output


class TestDomainRegistry:
    """Tests for DOMAIN_REGISTRY correctness."""

    def test_registry_contains_banking(self):
        """DOMAIN_REGISTRY has a 'banking' entry."""
        assert "banking" in DOMAIN_REGISTRY

    def test_registry_contains_healthcare(self):
        """DOMAIN_REGISTRY has a 'healthcare' entry."""
        assert "healthcare" in DOMAIN_REGISTRY

    def test_registry_contains_hr(self):
        """DOMAIN_REGISTRY has an 'hr' entry."""
        assert "hr" in DOMAIN_REGISTRY

    def test_registry_values_are_classes(self):
        """All values in DOMAIN_REGISTRY are class objects (not instances)."""
        for name, cls in DOMAIN_REGISTRY.items():
            assert isinstance(cls, type), f"{name} value should be a class"

    def test_registry_classes_can_be_instantiated(self):
        """All registered classes can be instantiated without arguments."""
        for name, cls in DOMAIN_REGISTRY.items():
            instance = cls()
            assert instance.name == name
