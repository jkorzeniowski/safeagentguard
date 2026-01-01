# app/run_agent.py

import os
import json
import sys
from typing import Any, Dict

import requests  # to be stubbed if the agent will call external API


"""
run_agent.py

This script is executed INSIDE the sandboxed Docker container.
Its responsibilities:

1. Load agent configuration from environment (AGENT_CONFIG, TEST_ID, SANDBOX_RULES).
2. Instantiate the agent (e.g., a simple OpenAI- or LangChain-based agent).
3. Expose a very small control surface for the sandbox:
   - receive a prompt/task (via stdin or env)
   - run the agent
   - print the result in a structured JSON format to stdout.

The sandbox supervisor (outside the container) interacts with this script
by:
- starting the container with proper env variables
- sending scenario-specific prompts
- reading the JSON output and checking for policy violations.
"""


def load_agent_config() -> Dict[str, Any]:
    """Load agent configuration from environment."""
    raw = os.environ.get("AGENT_CONFIG", "{}")
    try:
        cfg = json.loads(raw) if isinstance(raw, str) else raw
    except json.JSONDecodeError:
        cfg = {}
    return cfg


def load_sandbox_rules() -> Dict[str, Any]:
    """Parse sandbox rules (can be used inside the agent wrapper)."""
    raw = os.environ.get("SANDBOX_RULES", "")
    # Example: "read_only_db,no_network_outbound,max_cpu_1core"
    rules = [r.strip() for r in raw.split(",") if r.strip()]
    return {"rules": rules}


def get_test_context() -> Dict[str, Any]:
    """Get test-level context such as TEST_ID and scenario input."""
    test_id = os.environ.get("TEST_ID", "unknown-test")
    # Scenario input can be passed via STDIN (preferred) or ENV
    if not sys.stdin.isatty():
        stdin_data = sys.stdin.read().strip()
        if stdin_data:
            try:
                scenario_input = json.loads(stdin_data)
            except json.JSONDecodeError:
                scenario_input = {"raw_input": stdin_data}
        else:
            scenario_input = {}
    else:
        # Fallback: scenario input from env
        scenario_input_raw = os.environ.get("SCENARIO_INPUT", "{}")
        try:
            scenario_input = json.loads(scenario_input_raw)
        except json.JSONDecodeError:
            scenario_input = {}
    return {
        "test_id": test_id,
        "scenario_input": scenario_input,
    }


def dummy_agent_call(prompt: str, config: Dict[str, Any]) -> str:
    """
    Replace this with your real agent logic.

    For now, this is a very simple echo-like agent with a fake 'unsafe' behavior:
    - If prompt contains the word 'DELETE_DB', it pretends to execute a dangerous action.
    """
    # You could plug here:
    # - OpenAI ChatCompletion
    # - LangChain agent
    # - Any custom tool-using agent
    if "DELETE_DB" in prompt:
        return "EXECUTING: rm -rf /prod-db  # DANGEROUS_ACTION_SIMULATED"
    return f"AGENT_RESPONSE: {prompt[::-1]}"  # silly reverse-echo


def main():
    agent_config = load_agent_config()
    sandbox_rules = load_sandbox_rules()
    ctx = get_test_context()

    scenario_input = ctx["scenario_input"]
    prompt = scenario_input.get("prompt", "Hello from SafeAgentGuard sandbox.")

    # Here you would construct your real agent using agent_config
    # e.g., OpenAI model, tools, etc.
    # For now, we call a dummy agent:
    agent_output = dummy_agent_call(prompt, agent_config)

    # You can add structured metadata for sandbox analysis:
    result = {
        "test_id": ctx["test_id"],
        "prompt": prompt,
        "agent_output": agent_output,
        "agent_config": agent_config,
        "sandbox_rules": sandbox_rules,
        # Optional: a list of "actions" the agent tried to perform
        # so the outer sandbox can analyze them.
        "actions": [],
    }

    # Print as a single JSON line for the sandbox supervisor to parse
    print(json.dumps(result))


if __name__ == "__main__":
    main()
