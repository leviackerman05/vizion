import json

import httpx
import pytest
from vizion.examples import example_storyboard
from vizion.planner import PipelineError, plan_lesson
from vizion.settings import settings


def model_response(plan):
    return httpx.Response(200, json={"choices": [{"message": {"content": json.dumps(plan)}}]})


def mock_provider(monkeypatch, handler):
    original = httpx.Client
    monkeypatch.setattr(settings, "llm_provider", "groq")
    monkeypatch.setattr(settings, "groq_api_key", "test-provider-credential")
    monkeypatch.setattr(
        httpx, "Client", lambda **kwargs: original(transport=httpx.MockTransport(handler), **kwargs)
    )


def test_invalid_model_output_is_repaired_without_changing_the_topic(monkeypatch):
    requests = []
    valid = example_storyboard().model_dump()

    def provider(request):
        requests.append(json.loads(request.content))
        if len(requests) == 1:
            invalid = {**valid, "scenes": valid["scenes"][:1]}
            return model_response(invalid)
        return model_response(valid)

    mock_provider(monkeypatch, provider)
    plan, provenance = plan_lesson("Explain the parabola through squaring", "beginner")
    assert plan.title == valid["title"] and len(requests) == 2
    assert "lesson-plan-" in provenance
    assert requests[0]["response_format"]["json_schema"]["strict"] is True
    assert requests[1]["messages"][1] == requests[0]["messages"][1]
    assert "Preserve the requested topic" in requests[1]["messages"][-1]["content"]


def test_free_quota_exhaustion_is_bounded_and_never_substitutes_an_example(monkeypatch):
    calls = []
    mock_provider(monkeypatch, lambda request: calls.append(request) or httpx.Response(429))
    monkeypatch.setattr("vizion.planner.time.sleep", lambda _: None)
    with pytest.raises(PipelineError, match="quota"):
        plan_lesson("Explain the parabola through squaring", "beginner")
    assert len(calls) == 3


def test_rejected_provider_key_is_actionable_and_not_retried(monkeypatch):
    calls = []
    mock_provider(monkeypatch, lambda request: calls.append(request) or httpx.Response(401))
    with pytest.raises(PipelineError, match="API key"):
        plan_lesson("Explain the parabola through squaring", "beginner")
    assert len(calls) == 1
