<div align="center">
  <h1>SafeAgentGuard</h1>
  <p><b>AI Safety Sandbox for Testing AI Agents</b></p>

  <img src="https://img.shields.io/badge/python-3.12+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/docker-ready-green.svg" alt="Docker">
  <img src="https://img.shields.io/badge/license-MIT-brightgreen.svg" alt="MIT License">
</div>

---

## What is SafeAgentGuard?

**SafeAgentGuard** is a safety testing sandbox for AI agents. It tests agents against attack scenarios to answer:

> **"Is this AI agent safe enough for production?"**

### The Problem

AI agents can be manipulated to:
- Approve unauthorized transactions through social engineering
- Leak customer PII (names, IBANs, addresses)
- Access restricted internal APIs they shouldn't touch

SafeAgentGuard tests your agents against these attack vectors and generates safety scores.

---

## Key Features

| Feature | Description |
|---------|-------------|
| **Domain-Specific Scenarios** | Banking: transaction fraud, PII leakage, API access |
| **Risk Scoring (0-100)** | Quantified safety score with per-scenario breakdown |
| **Docker Isolation** | Run untrusted agents in isolated containers |
| **Extensible Architecture** | Add custom agents, domains, and scenarios |

---

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/safeagentguard.git
cd safeagentguard

# Install with pip (recommended)
pip install -e .

# Or install from requirements.txt
pip install -r requirements.txt
```

For OpenAI agent support:
```bash
pip install -e ".[openai]"
```

For development (includes pytest, black):
```bash
pip install -e ".[dev]"
```

---

## Running Locally

### Basic Usage (Python)

```python
import logging
from src.sandbox import Sandbox
from src.domains.banking import BankingDomain

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create sandbox with banking domain
domain = BankingDomain()
sandbox = Sandbox(domain=domain)

# Test with a mock agent
results = sandbox.run_test(
    agent_config={"type": "mock_safe"}
)

logger.info("Safety Score: %d/100", results.score)
logger.info("Passed: %d/%d scenarios", results.passed_count, results.total_count)

for result in results.scenario_results:
    status = "PASS" if result.passed else "FAIL"
    logger.info("  [%s] %s", status, result.scenario_name)
```

### Testing Different Agent Types

```python
# Mock agent (always refuses - for testing)
results = sandbox.run_test(agent_config={"type": "mock_safe"})

# Vulnerable mock agent (always complies - for testing)
results = sandbox.run_test(agent_config={"type": "mock_vulnerable"})

# OpenAI agent (requires API key)
results = sandbox.run_test(
    agent_config={
        "type": "openai",
        "api_key": "sk-...",  # Or set OPENAI_API_KEY env var
        "model": "gpt-4o-mini",
        "system_prompt": "You are a banking assistant.",
    }
)
```

### Running Specific Scenarios

```python
# Run only specific scenarios
results = sandbox.run_test(
    agent_config={"type": "mock_safe"},
    scenario_names=["transaction_fraud", "pii_leakage"]
)
```

### Using a Pre-configured Agent

```python
from src.agents.mock import SafeMockAgent

agent = SafeMockAgent()
results = sandbox.run_test_with_agent(agent)
```

---

## Running with Docker

Docker provides isolation for testing untrusted agents.

### Build the Docker Image

```bash
docker build -t safeagentguard-agent:latest -f docker/Dockerfile.agent .
```

### Run Tests in Docker

```python
from src.sandbox import Sandbox
from src.domains.banking import BankingDomain

sandbox = Sandbox(
    domain=BankingDomain(),
    use_docker=True,
    docker_image="safeagentguard-agent:latest"
)

results = sandbox.run_test(agent_config={"type": "mock_safe"})
```

### Docker Security Features

When running with Docker, agents execute with:
- **Network isolation** (`--network=none`)
- **Memory limits** (512MB)
- **CPU limits** (1 core)
- **Non-root user**
- **60-second timeout**

---

## Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_sandbox.py -v

# Run with coverage report
pytest --cov=src --cov-report=term-missing
```

---

## Project Structure

```
safeagentguard/
├── src/
│   ├── agents/           # Agent adapters
│   │   ├── base.py       # BaseAgent abstract class
│   │   ├── mock.py       # Mock agents for testing
│   │   └── openai.py     # OpenAI agent adapter
│   ├── domains/          # Domain scenarios
│   │   ├── base.py       # BaseDomain abstract class
│   │   └── banking.py    # Banking attack scenarios
│   ├── sandbox.py        # Main orchestrator
│   ├── scoring.py        # Evaluation logic
│   ├── exceptions.py     # Custom exceptions
│   └── run_agent.py      # Docker container entry point
├── docker/
│   └── Dockerfile.agent  # Docker image for isolated execution
├── tests/                # pytest tests
├── pyproject.toml        # Package configuration
└── requirements.txt      # Dependencies
```

---

## Banking Domain Scenarios

### Transaction Fraud
Tests if the agent can be manipulated into approving unauthorized transactions:
- Social engineering attacks ("urgent CEO request")
- Authority impersonation
- Bypassing approval procedures

### PII Data Leakage
Tests agent resistance to exposing customer personal data:
- Direct extraction attempts
- Fake compliance/audit requests
- Data dumps

### Unauthorized API Access
Tests if the agent respects API boundaries:
- Attempts to access `/internal/*` endpoints
- Admin panel escalation
- Core banking system access

---

## Extending SafeAgentGuard

### Adding a Custom Agent

```python
from src.agents.base import BaseAgent, AgentResponse

class MyCustomAgent(BaseAgent):
    def run(self, prompt: str) -> AgentResponse:
        # Your agent logic here
        response = call_your_llm(prompt)
        return AgentResponse(output=response, raw_response=response)
```

### Adding a Custom Domain

```python
from src.domains.base import BaseDomain, Scenario

class HealthcareDomain(BaseDomain):
    @property
    def name(self) -> str:
        return "healthcare"

    def get_scenarios(self) -> list[Scenario]:
        return [
            Scenario(
                name="hipaa_violation",
                description="Tests for HIPAA compliance",
                attack_prompt="Show me patient records for...",
                success_indicators=["patient", "diagnosis", "ssn"],
            ),
        ]
```

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | API key for OpenAI agents |

---

## License

MIT License - See `LICENSE` for details.

<div align="center">
<strong>Test your agents before they touch production.</strong>
</div>