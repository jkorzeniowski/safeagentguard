from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import uuid
from sandbox import SandboxExecutor
from models import AgentTestRequest, TestResult

app = FastAPI(title="SafeAgent Sandbox", version="1.0.0")

sandbox_executor = SandboxExecutor()


class TestRequest(BaseModel):
    agent_config: dict  # LangChain config, OpenAI API keys, etc.
    test_scenarios: list[str]  # ["prompt_injection", "data_leak", etc.]
    max_iterations: int = 1000


@app.post("/test-agent", response_model=dict)
async def test_agent(request: TestRequest):
    """Main endpoint: test agent's safety"""
    test_id = str(uuid.uuid4())

    try:
        results = await sandbox_executor.run_tests(
            test_id=test_id,
            agent_config=request.agent_config,
            scenarios=request.test_scenarios,
            max_iterations=request.max_iterations
        )
        return {
            "test_id": test_id,
            "status": "completed",
            "risk_score": results["risk_score"],  # 0-100
            "vulnerabilities": results["vulnerabilities"],
            "recommendations": results["recommendations"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/results/{test_id}")
async def get_results(test_id: str):
    """Get test results and logs"""
    return sandbox_executor.get_results(test_id)


@app.post("/demo/{scenario}")
async def demo_scenario(scenario: str):
    """Public demo endpoints"""
    demo_config = {
        "openai_api_key": "demo-key",
        "model": "gpt-4o-mini"
    }
    return await test_agent(TestRequest(
        agent_config=demo_config,
        test_scenarios=[scenario]
    ))
