"""Agent execution script for running inside Docker containers.

This script is the entry point for agent execution in the sandbox.
It reads configuration from environment/stdin and outputs JSON results.
"""

import json
import os
import sys

from src.agents.base import BaseAgent
from src.agents.mock import MockAgent, SafeMockAgent, VulnerableMockAgent
from src.exceptions import AgentConfigError, AgentExecutionError
from src.logging_config import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)


def get_agent_from_config(config: dict) -> BaseAgent:
    """Create an agent instance from configuration.

    Args:
        config: Agent configuration dictionary with 'type' key.

    Returns:
        A BaseAgent instance.

    Raises:
        AgentConfigError: If agent type is not supported or config is invalid.
    """
    if not isinstance(config, dict):
        raise AgentConfigError("Agent config must be a dictionary")

    agent_type = config.get("type", "mock")

    if agent_type == "mock":
        return MockAgent(default_response=config.get("response", "I cannot help."))
    elif agent_type == "mock_vulnerable":
        return VulnerableMockAgent()
    elif agent_type == "mock_safe":
        return SafeMockAgent()
    elif agent_type == "openai":
        from src.agents.openai import OpenAIAgent

        api_key = config.get("api_key", os.environ.get("OPENAI_API_KEY", ""))
        if not api_key:
            raise AgentConfigError(
                "OpenAI agent requires 'api_key' in config or OPENAI_API_KEY env var"
            )
        return OpenAIAgent(
            api_key=api_key,
            model=config.get("model", "gpt-4o-mini"),
            system_prompt=config.get("system_prompt"),
        )
    else:
        raise AgentConfigError(f"Unsupported agent type: {agent_type}")


def run_agent(agent_config: dict, prompt: str) -> dict:
    """Execute an agent with the given prompt.

    Args:
        agent_config: Configuration for creating the agent.
        prompt: The prompt to send to the agent.

    Returns:
        Dictionary with 'output', 'success', and optional 'error' keys.
    """
    try:
        agent = get_agent_from_config(agent_config)
        response = agent.run(prompt)
        return {
            "output": response.output,
            "success": True,
            "raw_response": response.raw_response,
        }
    except AgentConfigError as e:
        logger.error("Invalid agent configuration: %s", e)
        return {
            "output": "",
            "success": False,
            "error": f"Configuration error: {e}",
        }
    except AgentExecutionError as e:
        logger.error("Agent execution failed: %s", e, exc_info=True)
        return {
            "output": "",
            "success": False,
            "error": f"Execution error: {e}",
        }
    except (TypeError, KeyError, AttributeError) as e:
        logger.error("Invalid input or response format: %s", e, exc_info=True)
        return {
            "output": "",
            "success": False,
            "error": f"Format error: {e}",
        }


def main():
    """Main entry point for container execution.

    Reads JSON input from stdin with format:
    {
        "agent_config": {...},
        "prompt": "..."
    }

    Outputs JSON result to stdout.
    """
    try:
        input_data = json.loads(sys.stdin.read())
        agent_config = input_data.get("agent_config", {})
        prompt = input_data.get("prompt", "")

        logger.info("Running agent with type: %s", agent_config.get("type", "unknown"))
        result = run_agent(agent_config, prompt)

        logger.debug("Agent execution result: %s", result)
        print(json.dumps(result))
    except json.JSONDecodeError as e:
        logger.error("Invalid JSON input: %s", e)
        error_response = {"success": False, "error": f"Invalid JSON input: {e}"}
        logger.debug("Error response: %s", error_response)
        print(json.dumps(error_response))
        sys.exit(1)
    except (KeyError, TypeError) as e:
        logger.error("Malformed input data: %s", e)
        error_response = {"success": False, "error": f"Malformed input: {e}"}
        logger.debug("Error response: %s", error_response)
        print(json.dumps(error_response))
        sys.exit(1)


if __name__ == "__main__":
    main()
