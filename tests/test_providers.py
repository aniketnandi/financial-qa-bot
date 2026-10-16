"""Provider layer and agent loop, with fake LLM clients (no network, no keys)."""
import json
from types import SimpleNamespace as NS

import httpx2
import openai
import pytest
from fastapi.testclient import TestClient

import agent
import llm
import main


@pytest.fixture
def azure(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "azure_openai")
    monkeypatch.setenv("AZURE_OPENAI_DEPLOYMENT", "test-deployment")
    llm._clients.clear()
    yield
    llm._clients.clear()


class FakeChat:
    """Stands in for AzureOpenAI: returns the scripted messages in order."""

    def __init__(self, *messages):
        self.messages, self.calls = list(messages), []
        self.chat = NS(completions=self)

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return NS(choices=[NS(message=self.messages.pop(0))])


def tool_call(id, name, **args):
    return NS(id=id, function=NS(name=name, arguments=json.dumps(args)))


def test_provider_defaults_to_gemini(monkeypatch):
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    assert llm.provider() == "gemini"


def test_unknown_provider_is_rejected(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "bedrock")
    with pytest.raises(ValueError):
        llm.provider()


def test_azure_agent_chains_tool_calls(azure, monkeypatch):
    fake = FakeChat(
        NS(content=None, tool_calls=[tool_call("c1", "calculate_growth", current=96773, previous=81462)]),
        NS(content="Revenue grew 18.80%.", tool_calls=None),
    )
    llm._clients["azure_openai"] = fake

    result = agent.run_agent("What was revenue growth?")

    assert result["answer"] == "Revenue grew 18.80%."
    assert result["trace"] == [{"tool": "calculate_growth",
                                "args": {"current": 96773, "previous": 81462}, "result": "18.80%"}]
    # Second request carries the assistant tool call and the tool result back to the model
    sent = fake.calls[1]["messages"]
    assert sent[-2]["tool_calls"][0]["id"] == "c1"
    assert sent[-1] == {"role": "tool", "tool_call_id": "c1", "content": "18.80%"}
    assert fake.calls[0]["model"] == "test-deployment"


def test_azure_agent_reports_bad_tool_calls_to_the_model(azure):
    fake = FakeChat(
        NS(content=None, tool_calls=[tool_call("c1", "delete_everything")]),
        NS(content="Done.", tool_calls=None),
    )
    llm._clients["azure_openai"] = fake
    assert agent.run_agent("q")["trace"][0]["result"] == "Unknown tool: delete_everything"


def test_azure_rag_generation(azure):
    llm._clients["azure_openai"] = FakeChat(NS(content="$96,773 million", tool_calls=None))
    assert llm.generate("prompt") == "$96,773 million"


def test_openai_rate_limit_maps_to_http_429(azure, monkeypatch):
    class RateLimited:
        def create(self, **kwargs):
            raise openai.RateLimitError(
                "slow down", body=None,
                response=httpx2.Response(429, request=httpx2.Request("POST", "http://aoai")))

    llm._clients["azure_openai"] = NS(chat=NS(completions=RateLimited()))
    monkeypatch.setattr(main.os.path, "exists", lambda path: True)

    resp = TestClient(main.app).post("/ask_agent", json={"question": "Revenue growth?"})
    assert resp.status_code == 429


def test_connection_failure_maps_to_503():
    err = llm.to_upstream_error(openai.APIConnectionError(request=httpx2.Request("POST", "http://aoai")))
    assert main.upstream_error(err).status_code == 503


def test_api_key_is_enforced_only_when_configured(monkeypatch):
    client = TestClient(main.app)
    monkeypatch.setenv("API_KEY", "s3cret")
    assert client.post("/ask", json={"question": " "}).status_code == 401
    assert client.post("/ask", json={"question": " "}, headers={"X-API-Key": "wrong"}).status_code == 401
    assert client.post("/ask", json={"question": " "}, headers={"X-API-Key": "s3cret"}).status_code == 400
    assert client.get("/").status_code == 200  # health check stays open
    monkeypatch.delenv("API_KEY")
    assert client.post("/ask", json={"question": " "}).status_code == 400


def test_gemini_agent_chains_tool_calls(monkeypatch):
    from google.genai import types

    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    call = types.FunctionCall(name="calculate_margin", args={"profit": 14974, "revenue": 96773})
    turns = [
        NS(candidates=[NS(content=types.Content(role="model", parts=[types.Part(function_call=call)]))], text=None),
        NS(candidates=[NS(content=types.Content(role="model", parts=[types.Part(text="Net margin was 15.47%.")]))],
           text="Net margin was 15.47%."),
    ]
    sent = []

    def generate_content(model, contents, config):
        sent.append(list(contents))
        return turns.pop(0)

    monkeypatch.setitem(llm._clients, "gemini", NS(models=NS(generate_content=generate_content)))

    result = agent.run_agent("Net margin?")

    assert result["answer"] == "Net margin was 15.47%."
    assert result["trace"] == [{"tool": "calculate_margin",
                                "args": {"profit": 14974, "revenue": 96773}, "result": "15.47%"}]
    tool_reply = sent[1][-1].parts[0].function_response
    assert tool_reply.name == "calculate_margin" and tool_reply.response == {"result": "15.47%"}
