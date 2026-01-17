"""OpenAI API agent adapter."""

from typing import Any

from src.agents.base import AgentResponse, BaseAgent
from src.exceptions import AgentAPIError, AgentConfigError
from src.logging_config import get_logger

logger = get_logger(__name__)


class OpenAIAgent(BaseAgent):
    """Agent adapter for OpenAI API (chat completions).

    Requires the 'openai' package to be installed.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ):
        """Initialize the OpenAI agent.

        Args:
            api_key: OpenAI API key.
            model: Model to use (default: gpt-4o-mini).
            system_prompt: Optional system prompt to set agent behavior.
            temperature: Sampling temperature (0-2).
            max_tokens: Maximum tokens in response.
        """
        self._api_key = api_key
        self._model = model
        self._system_prompt = system_prompt
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._client: Any = None

    def _get_client(self):
        """Lazily initialize the OpenAI client.

        Raises:
            AgentConfigError: If openai package is not installed.
        """
        if self._client is None:
            try:
                from openai import OpenAI

                self._client = OpenAI(api_key=self._api_key)
            except ImportError as e:
                raise AgentConfigError(
                    "openai package is required for OpenAIAgent. "
                    "Install it with: pip install openai"
                ) from e
        return self._client

    def run(self, prompt: str) -> AgentResponse:
        """Execute the OpenAI agent with the given prompt.

        Args:
            prompt: The input prompt to send to the model.

        Returns:
            AgentResponse containing the model's output.

        Raises:
            AgentAPIError: If the API call fails.
        """
        client = self._get_client()

        messages = []
        if self._system_prompt:
            messages.append({"role": "system", "content": self._system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = client.chat.completions.create(
                model=self._model,
                messages=messages,
                temperature=self._temperature,
                max_tokens=self._max_tokens,
            )

            output = response.choices[0].message.content or ""

            return AgentResponse(
                output=output,
                raw_response={
                    "id": response.id,
                    "model": response.model,
                    "usage": (
                        {
                            "prompt_tokens": response.usage.prompt_tokens,
                            "completion_tokens": response.usage.completion_tokens,
                        }
                        if response.usage
                        else None
                    ),
                },
            )

        except (AttributeError, IndexError, KeyError) as e:
            logger.error("Unexpected API response format: %s", e, exc_info=True)
            raise AgentAPIError(f"Unexpected API response format: {e}") from e
        except OSError as e:
            logger.error("Network error during OpenAI API call: %s", e, exc_info=True)
            raise AgentAPIError(f"Network error: {e}") from e
