"""Tests for src/agents/openai.py (OpenAIAgent class).

Coverage targets:
- __init__ parameter storage
- _get_client: lazy init, ImportError -> AgentConfigError, cached client
- run: happy path, system prompt, no system prompt, usage stats, null usage,
       OSError -> AgentAPIError, AttributeError -> AgentAPIError,
       IndexError -> AgentAPIError, KeyError -> AgentAPIError
"""

import sys
from types import ModuleType
from unittest.mock import MagicMock, patch

import pytest

from src.agents.base import AgentResponse
from src.exceptions import AgentAPIError, AgentConfigError

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mock_response(
    content: str = "Hello!",
    response_id: str = "chatcmpl-abc123",
    model: str = "gpt-4o-mini",
    prompt_tokens: int = 10,
    completion_tokens: int = 20,
    include_usage: bool = True,
) -> MagicMock:
    """Build a realistic mock openai ChatCompletion response object."""
    response = MagicMock()
    response.id = response_id
    response.model = model

    message = MagicMock()
    message.content = content

    choice = MagicMock()
    choice.message = message

    response.choices = [choice]

    if include_usage:
        usage = MagicMock()
        usage.prompt_tokens = prompt_tokens
        usage.completion_tokens = completion_tokens
        response.usage = usage
    else:
        response.usage = None

    return response


def _make_agent(
    api_key: str = "sk-test-key",
    model: str = "gpt-4o-mini",
    system_prompt: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 1024,
):
    """Import and instantiate OpenAIAgent. Deferred to avoid top-level import
    issues when openai is not installed in the test environment."""
    from src.agents.openai import OpenAIAgent

    return OpenAIAgent(
        api_key=api_key,
        model=model,
        system_prompt=system_prompt,
        temperature=temperature,
        max_tokens=max_tokens,
    )


# ---------------------------------------------------------------------------
# Test classes
# ---------------------------------------------------------------------------


class TestOpenAIAgentInit:
    """Tests for OpenAIAgent.__init__ parameter storage."""

    def test_stores_api_key(self):
        agent = _make_agent(api_key="sk-secret")
        assert agent._api_key == "sk-secret"

    def test_default_model(self):
        agent = _make_agent()
        assert agent._model == "gpt-4o-mini"

    def test_custom_model(self):
        agent = _make_agent(model="gpt-4o")
        assert agent._model == "gpt-4o"

    def test_default_system_prompt_is_none(self):
        agent = _make_agent()
        assert agent._system_prompt is None

    def test_custom_system_prompt_stored(self):
        agent = _make_agent(system_prompt="You are a helpful assistant.")
        assert agent._system_prompt == "You are a helpful assistant."

    def test_default_temperature(self):
        agent = _make_agent()
        assert agent._temperature == 0.7

    def test_custom_temperature(self):
        agent = _make_agent(temperature=0.0)
        assert agent._temperature == 0.0

    def test_default_max_tokens(self):
        agent = _make_agent()
        assert agent._max_tokens == 1024

    def test_custom_max_tokens(self):
        agent = _make_agent(max_tokens=512)
        assert agent._max_tokens == 512

    def test_client_initially_none(self):
        agent = _make_agent()
        assert agent._client is None


class TestGetClient:
    """Tests for OpenAIAgent._get_client lazy initialisation."""

    def test_raises_agent_config_error_when_openai_not_installed(self):
        """AgentConfigError must be raised if the openai package is absent."""
        agent = _make_agent()

        with patch.dict(sys.modules, {"openai": None}):
            with pytest.raises(AgentConfigError, match="openai package is required"):
                agent._get_client()

    def test_raises_agent_config_error_message_contains_install_hint(self):
        agent = _make_agent()

        with patch.dict(sys.modules, {"openai": None}):
            with pytest.raises(AgentConfigError, match="pip install openai"):
                agent._get_client()

    def test_client_created_with_api_key(self):
        agent = _make_agent(api_key="sk-my-key")

        mock_openai_module = ModuleType("openai")
        mock_client_instance = MagicMock()
        mock_openai_class = MagicMock(return_value=mock_client_instance)
        mock_openai_module.OpenAI = mock_openai_class

        with patch.dict(sys.modules, {"openai": mock_openai_module}):
            client = agent._get_client()

        mock_openai_class.assert_called_once_with(api_key="sk-my-key")
        assert client is mock_client_instance

    def test_client_is_cached_after_first_call(self):
        """_get_client must return the same object on subsequent calls."""
        agent = _make_agent()

        mock_openai_module = ModuleType("openai")
        mock_client_instance = MagicMock()
        mock_openai_class = MagicMock(return_value=mock_client_instance)
        mock_openai_module.OpenAI = mock_openai_class

        with patch.dict(sys.modules, {"openai": mock_openai_module}):
            first = agent._get_client()
            second = agent._get_client()

        assert first is second
        mock_openai_class.assert_called_once()  # constructed only once

    def test_already_set_client_is_returned_without_import(self):
        """If _client is already set, openai is never imported again."""
        agent = _make_agent()
        pre_existing = MagicMock()
        agent._client = pre_existing

        # openai is absent — should NOT raise because the import is skipped
        with patch.dict(sys.modules, {"openai": None}):
            client = agent._get_client()

        assert client is pre_existing


class TestRunHappyPath:
    """Tests for OpenAIAgent.run successful execution."""

    def _run_with_mock_response(
        self,
        mock_response: MagicMock,
        system_prompt: str | None = None,
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> tuple[AgentResponse, MagicMock]:
        """Helper that injects a mock client and calls run."""
        agent = _make_agent(
            model=model,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        agent._client = mock_client
        response = agent.run("test prompt")
        return response, mock_client

    def test_returns_agent_response_instance(self):
        mock_resp = _make_mock_response(content="Hello!")
        response, _ = self._run_with_mock_response(mock_resp)
        assert isinstance(response, AgentResponse)

    def test_output_contains_model_content(self):
        mock_resp = _make_mock_response(content="Paris is the capital of France.")
        response, _ = self._run_with_mock_response(mock_resp)
        assert response.output == "Paris is the capital of France."

    def test_raw_response_contains_id(self):
        mock_resp = _make_mock_response(response_id="chatcmpl-xyz")
        response, _ = self._run_with_mock_response(mock_resp)
        assert response.raw_response["id"] == "chatcmpl-xyz"

    def test_raw_response_contains_model(self):
        mock_resp = _make_mock_response(model="gpt-4o")
        response, _ = self._run_with_mock_response(mock_resp, model="gpt-4o")
        assert response.raw_response["model"] == "gpt-4o"

    def test_raw_response_usage_stats_present(self):
        mock_resp = _make_mock_response(
            prompt_tokens=15, completion_tokens=30, include_usage=True
        )
        response, _ = self._run_with_mock_response(mock_resp)
        usage = response.raw_response["usage"]
        assert usage == {"prompt_tokens": 15, "completion_tokens": 30}

    def test_raw_response_usage_is_none_when_api_returns_no_usage(self):
        mock_resp = _make_mock_response(include_usage=False)
        response, _ = self._run_with_mock_response(mock_resp)
        assert response.raw_response["usage"] is None

    def test_empty_content_falls_back_to_empty_string(self):
        """When choices[0].message.content is falsy, output should be ''."""
        mock_resp = _make_mock_response(content="")
        # Override: the ``or ""`` guard should kick in
        mock_resp.choices[0].message.content = None
        response, _ = self._run_with_mock_response(mock_resp)
        assert response.output == ""


class TestRunSystemPrompt:
    """Tests for system prompt inclusion in the messages list."""

    def _capture_messages(
        self, system_prompt: str | None, prompt: str = "user question"
    ) -> list[dict]:
        """Run the agent and return the messages passed to the API."""
        mock_resp = _make_mock_response()
        agent = _make_agent(system_prompt=system_prompt)
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_resp
        agent._client = mock_client

        agent.run(prompt)

        call_kwargs = mock_client.chat.completions.create.call_args
        return call_kwargs.kwargs["messages"]

    def test_no_system_prompt_sends_only_user_message(self):
        messages = self._capture_messages(system_prompt=None)
        assert len(messages) == 1
        assert messages[0] == {"role": "user", "content": "user question"}

    def test_with_system_prompt_sends_two_messages(self):
        messages = self._capture_messages(system_prompt="You are a bank assistant.")
        assert len(messages) == 2

    def test_system_message_is_first(self):
        messages = self._capture_messages(system_prompt="Be concise.")
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "Be concise."

    def test_user_message_is_last(self):
        messages = self._capture_messages(
            system_prompt="Be concise.", prompt="What is 2+2?"
        )
        assert messages[-1] == {"role": "user", "content": "What is 2+2?"}

    def test_empty_string_system_prompt_not_included(self):
        """An empty string is falsy; it should NOT add a system message."""
        messages = self._capture_messages(system_prompt="")
        assert len(messages) == 1
        assert messages[0]["role"] == "user"


class TestRunAPIParameters:
    """Tests that run() forwards constructor params to the API call."""

    def _get_create_call_kwargs(
        self,
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> dict:
        mock_resp = _make_mock_response()
        agent = _make_agent(model=model, temperature=temperature, max_tokens=max_tokens)
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_resp
        agent._client = mock_client
        agent.run("prompt")
        return mock_client.chat.completions.create.call_args.kwargs

    def test_model_forwarded(self):
        kwargs = self._get_create_call_kwargs(model="gpt-4o")
        assert kwargs["model"] == "gpt-4o"

    def test_temperature_forwarded(self):
        kwargs = self._get_create_call_kwargs(temperature=0.0)
        assert kwargs["temperature"] == 0.0

    def test_max_tokens_forwarded(self):
        kwargs = self._get_create_call_kwargs(max_tokens=256)
        assert kwargs["max_tokens"] == 256


class TestRunErrorHandling:
    """Tests for error paths in OpenAIAgent.run."""

    def _agent_with_raising_client(self, side_effect: Exception) -> "OpenAIAgent":
        from src.agents.openai import OpenAIAgent

        agent = OpenAIAgent(api_key="sk-key")
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = side_effect
        agent._client = mock_client
        return agent

    def test_os_error_raises_agent_api_error(self):
        agent = self._agent_with_raising_client(OSError("Connection refused"))
        with pytest.raises(AgentAPIError, match="Network error"):
            agent.run("prompt")

    def test_os_error_original_message_in_exception(self):
        agent = self._agent_with_raising_client(OSError("DNS lookup failed"))
        with pytest.raises(AgentAPIError, match="DNS lookup failed"):
            agent.run("prompt")

    def test_os_error_chained_exception(self):
        original = OSError("timeout")
        agent = self._agent_with_raising_client(original)
        with pytest.raises(AgentAPIError) as exc_info:
            agent.run("prompt")
        assert exc_info.value.__cause__ is original

    def test_attribute_error_raises_agent_api_error(self):
        """AttributeError from malformed response -> AgentAPIError."""
        agent = self._agent_with_raising_client(
            AttributeError("'NoneType' has no attribute 'choices'")
        )
        with pytest.raises(AgentAPIError, match="Unexpected API response format"):
            agent.run("prompt")

    def test_index_error_raises_agent_api_error(self):
        """IndexError when choices list is empty -> AgentAPIError."""
        agent = self._agent_with_raising_client(IndexError("list index out of range"))
        with pytest.raises(AgentAPIError, match="Unexpected API response format"):
            agent.run("prompt")

    def test_key_error_raises_agent_api_error(self):
        """KeyError from unexpected response shape -> AgentAPIError."""
        agent = self._agent_with_raising_client(KeyError("content"))
        with pytest.raises(AgentAPIError, match="Unexpected API response format"):
            agent.run("prompt")

    def test_attribute_error_chained_exception(self):
        original = AttributeError("bad attr")
        agent = self._agent_with_raising_client(original)
        with pytest.raises(AgentAPIError) as exc_info:
            agent.run("prompt")
        assert exc_info.value.__cause__ is original

    def test_index_error_chained_exception(self):
        original = IndexError("out of range")
        agent = self._agent_with_raising_client(original)
        with pytest.raises(AgentAPIError) as exc_info:
            agent.run("prompt")
        assert exc_info.value.__cause__ is original

    def test_key_error_chained_exception(self):
        original = KeyError("missing_key")
        agent = self._agent_with_raising_client(original)
        with pytest.raises(AgentAPIError) as exc_info:
            agent.run("prompt")
        assert exc_info.value.__cause__ is original

    def test_attribute_error_on_response_field_access(self):
        """AttributeError raised when choices[0] has no .message attribute."""
        from src.agents.openai import OpenAIAgent

        class _NoMessage:
            """Object whose .message access raises AttributeError."""

            @property
            def message(self):
                raise AttributeError("object has no attribute 'message'")

        agent = OpenAIAgent(api_key="sk-key")
        mock_resp = MagicMock()
        mock_resp.choices = [_NoMessage()]
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_resp
        agent._client = mock_client

        with pytest.raises(AgentAPIError, match="Unexpected API response format"):
            agent.run("prompt")

    def test_empty_choices_list_raises_agent_api_error(self):
        """An empty choices list causes IndexError -> AgentAPIError."""
        from src.agents.openai import OpenAIAgent

        agent = OpenAIAgent(api_key="sk-key")
        mock_resp = MagicMock()
        mock_resp.choices = []  # real list, but empty
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_resp
        agent._client = mock_client

        with pytest.raises(AgentAPIError, match="Unexpected API response format"):
            agent.run("prompt")
