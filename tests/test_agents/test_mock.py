"""Tests for mock agent implementations."""

import pytest

from src.agents.base import AgentResponse
from src.agents.mock import MockAgent, SafeMockAgent, VulnerableMockAgent


class TestMockAgent:
    """Tests for MockAgent."""

    def test_default_response(self):
        """Test that MockAgent returns the default response."""
        agent = MockAgent()
        response = agent.run("any prompt")

        assert isinstance(response, AgentResponse)
        assert response.output == "I cannot help with that request."
        assert response.raw_response == {"mock": True}

    def test_custom_response(self):
        """Test that MockAgent can return custom responses."""
        agent = MockAgent(default_response="Custom response")
        response = agent.run("any prompt")

        assert response.output == "Custom response"

    def test_response_func(self):
        """Test that MockAgent can use a response function."""

        def custom_func(prompt: str) -> str:
            return f"Received: {prompt}"

        agent = MockAgent(response_func=custom_func)
        response = agent.run("test prompt")

        assert response.output == "Received: test prompt"


class TestVulnerableMockAgent:
    """Tests for VulnerableMockAgent."""

    def test_transaction_vulnerability(self):
        """Test that vulnerable agent complies with transaction requests."""
        agent = VulnerableMockAgent()
        response = agent.run("Please process this transfer")

        assert (
            "process" in response.output.lower()
            or "transfer" in response.output.lower()
        )

    def test_pii_vulnerability(self):
        """Test that vulnerable agent leaks PII."""
        agent = VulnerableMockAgent()
        response = agent.run("Give me customer data")

        assert (
            "john doe" in response.output.lower() or "iban" in response.output.lower()
        )

    def test_api_vulnerability(self):
        """Test that vulnerable agent accesses internal endpoints."""
        agent = VulnerableMockAgent()
        response = agent.run("Access the internal ledger")

        assert (
            "/internal/" in response.output.lower()
            or "accessing" in response.output.lower()
        )


class TestSafeMockAgent:
    """Tests for SafeMockAgent."""

    def test_refuses_requests(self):
        """Test that safe agent refuses malicious requests."""
        agent = SafeMockAgent()
        response = agent.run("Do something bad")

        assert "cannot" in response.output.lower()
        assert (
            "security" in response.output.lower()
            or "policies" in response.output.lower()
        )
