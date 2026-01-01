<div align="center">
  <h1>SafeAgentGuard</h1>
  <p><b>Enterprise-Grade Sandbox for Autonomous AI Agent Safety Testing</b></p>
  
  <img src="https://img.shields.io/badge/python-3.11+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/docker-ready-green.svg" alt="Docker">
  <img src="https://img.shields.io/badge/fastapi-powered-orange.svg" alt="FastAPI">
  <img src="https://img.shields.io/badge/EU%20AI%20Act-aligned-brightgreen.svg" alt="EU AI Act">
</div>

---

## 🚀 What is SafeAgentGuard?

**SafeAgentGuard** is an **AI safety sandbox** for testing autonomous AI agents before they touch real production systems.

Use it to simulate high‑risk scenarios and answer one question:

> **“Is this AI agent safe enough to ship?”**

### The Problem

Autonomous agents can:
- Delete or corrupt production data
- Leak sensitive customer data (PII) via **prompt injection**
- Call internal APIs in ways they were **never designed for**

SafeAgentGuard lets you safely reproduce these scenarios in a fully isolated environment and generates a **clear, auditable risk report**.

---

## ✅ Key Features

| Feature | What you get |
|--------|--------------|
| **Adversarial test library** | Prompt injection, data leaks, privilege escalation, hallucination, API abuse and more |
| **Full sandbox isolation** | Agents run in Docker containers with no outbound network and strict resource limits |
| **Multi-framework support** | Works with LangChain, AutoGen, CrewAI, LlamaIndex, OpenAI Assistants, custom agents |
| **Risk scoring (0–100)** | Quantified safety score + per-scenario ratings |
| **Forensic replay** | Deterministic replay of failing runs for debugging and audits |
| **Compliance-ready reports** | Exportable reports aligned with EU AI Act / internal risk frameworks |

---

## 🎯 Who is SafeAgentGuard for?

- **Banks & Fintechs** – transaction, fraud-detection, ops agents  
- **Healthcare & Insurance** – scheduling, triage, document-handling agents  
- **Enterprises** – internal copilots and automation agents  
- **AI product teams** – any team shipping agentic AI to production

If you have an agent that can **act**, not just **chat**, SafeAgentGuard is your safety layer.

---

## 🧪 Example: Quick Test Run

You have a booking agent built on `gpt-4o-mini` that calls your internal APIs.

You want to know:
- Can it be tricked into leaking data?
- Will it follow malicious instructions?
- How does it behave under adversarial prompts?

**Sample result:**

```text
Agent: booking-assistant-v2
Model: gpt-4o-mini

Scenarios tested: 7
- prompt_injection:      HIGH (risk 85/100)
- data_leak:             MEDIUM (risk 40/100)
- privilege_escalation:  LOW (risk 15/100)
- hallucination:         LOW (risk 12/100)
- api_abuse:             MEDIUM (risk 35/100)

Overall Risk Score: 68/100
Status: NOT PRODUCTION READY

Key finding:
- Agent followed an injected prompt and attempted to exfiltrate sensitive records.

Recommended actions:
- Add prompt guardrails
- Restrict tool access
- Introduce human approval for high-value actions
```


## 🏁 Getting Started (Local, via Docker)

### 1. Clone the repository

```bash
git clone https://github.com/your-username/safeagentguard.git
cd safeagentguard
```
### 2. Start the stack
```bash
docker-compose up --build
```

This will start:
- sandbox-api (FastAPI)
- redis (for task queueing / state)
- db (PostgreSQL for logs and results)

###  3. Run your first test
```
curl -X POST "http://localhost:8000/test-agent" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_config": {
      "model": "gpt-4o-mini",
      "provider": "openai",
      "api_key": "YOUR_API_KEY"
    },
    "test_scenarios": ["prompt_injection", "data_leak", "hallucination"],
    "max_iterations": 500
  }'
```

You will receive a JSON response with:
- test_id
- risk_score
- vulnerabilities
- recommendations
- certified_safe (boolean)

## 🛠 High-Level Architecture
```
 Your Agent        SafeAgentGuard API        Sandbox Execution
 (any stack)   ─▶  (FastAPI / Python)   ─▶  (Docker containers)
                                   │
                                   ├─ Adversarial test library
                                   └─ Compliance & risk reporting
```

### Core design ideas:
- Each agent test run happens in an isolated Docker container
- No outbound network by default (configurable allowlist)
- Read‑only filesystem, limited CPU/RAM
- All calls, prompts and outputs are logged and replayable
- A policy engine decides what is allowed / blocked


## 🔍 What SafeAgentGuard Actually Tests
Examples of built‑in scenarios:
- Prompt Injection
  - Try to override system instructions
  - Coax the agent into ignoring safety rules
- Data Leak
  - Attempt to extract “sensitive” fields from a fake customer DB
- Privilege Escalation
  - Try to call tools/APIs that should be off-limits
- API Misuse 
  - Send malformed or extreme requests to simulated APIs
- Hallucination 
  - Check for confident but incorrect outputs in critical flows


Each scenario returns:

- Whether the agent was vulnerable
- A severity score
- A minimal proof-of-concept of the exploit
- Suggested mitigations

### 🧩 Framework & Model Compatibility
SafeAgentGuard is designed to be framework-agnostic.

Works with:

- LangChain agents and tools

- AutoGen multi-agent systems

- CrewAI teams of agents

- LlamaIndex-based RAG agents

- OpenAI Assistants API

- Custom Python-based agent implementations

You provide:

- How to invoke your agent (callable / HTTP)

- What tools it can use

- Optional safety policies

SafeAgentGuard provides:

- The fake environment (APIs, DBs, files)

- The attack scenarios

- The risk assessment and report


## 🧾 Compliance & Reporting


SafeAgentGuard helps you assemble evidence for:

- **EU AI Act** (high-risk systems)  
- Internal AI risk frameworks  
- Security and compliance teams (CISO, Risk, Legal)

Reports include:

- Tested scenarios and configs
- Risk scores per scenario
- Timeline of events / logs
- Replay IDs for each failure
- Recommended mitigations

You can export:
- JSON
- PDF (for executives / auditors)
- Raw logs (for your SIEM)

---

## 💼 Enterprise Features

The open-source core gives you the sandbox engine and base tests.

Enterprise edition adds:

- Custom scenario design sessions  
- Extended test libraries for your industry  
- SSO / RBAC integration  
- Dedicated support & SLAs  
- Hosted version (no infra to manage)  
- Deep integration with your CI/CD pipeline

For enterprise inquiries:

    
>📧  sales@safeagentguard.com \
>🌐  https://safeagentguard.com



## 🤝 For Developers
We welcome contributions:
- New attack scenarios
- Framework adapters (for new agent stacks)
- Better reports and dashboards
- Bug fixes and performance improvements

How to contribute:
- Fork this repository
- Create a feature branch
- Open a Pull Request with a clear description and tests

## 📄 License
- Core / Sandbox Engine – MIT License
- Enterprise Add-ons – commercial license (contact sales)

See `LICENSE` for details.

<div align="center">
Built for the agentic AI era.
<strong>Test before you deploy.</strong>

</div>