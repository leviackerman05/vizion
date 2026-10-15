import json

import httpx
import pytest
from vizion.examples import example_storyboard
from vizion.planner import PipelineError, plan_lesson
from vizion.settings import settings


def model_response(content):
    return httpx.Response(200, json={"choices": [{"message": {"content": json.dumps(content)}}]})


def mock_provider(monkeypatch, handler):
    original = httpx.Client
    monkeypatch.setattr(settings, "llm_provider", "groq")
    monkeypatch.setattr(settings, "groq_api_key", "test-provider-credential")
    monkeypatch.setattr(
        httpx, "Client", lambda **kwargs: original(transport=httpx.MockTransport(handler), **kwargs)
    )


def is_review(body):
    return body["response_format"]["type"] == "json_object"


def test_invalid_draft_is_repaired_then_independently_reviewed(monkeypatch):
    requests = []
    valid = example_storyboard().model_dump()

    def provider(request):
        body = json.loads(request.content)
        requests.append(body)
        if is_review(body):
            return model_response({"approved": True, "issues": []})
        return model_response({**valid, "scenes": valid["scenes"][:1]} if len(requests) == 1 else valid)

    mock_provider(monkeypatch, provider)
    plan, provenance = plan_lesson("Explain the parabola through squaring", "beginner")
    assert plan.title == valid["title"] and len(requests) == 3
    assert "lesson-plan-" in provenance
    assert requests[0]["response_format"]["json_schema"]["strict"] is True
    assert requests[1]["messages"][1] == requests[0]["messages"][1]
    assert "Preserve the requested topic" in requests[1]["messages"][-1]["content"]
    assert is_review(requests[2]) and requests[2]["reasoning_effort"] == "high"


def test_critic_issues_are_repaired_and_checked_again(monkeypatch):
    valid = example_storyboard().model_dump()
    requests, reviews = [], []

    def provider(request):
        body = json.loads(request.content)
        requests.append(body)
        if is_review(body):
            reviews.append(body)
            return model_response(
                {
                    "approved": len(reviews) > 1,
                    "issues": [] if len(reviews) > 1 else ["Correct the example arithmetic."],
                }
            )
        return model_response({**valid, "title": "Reviewed explanation"} if len(requests) > 1 else valid)

    mock_provider(monkeypatch, provider)
    plan, _ = plan_lesson("Explain the parabola through squaring", "beginner")
    assert plan.title == "Reviewed explanation" and len(requests) == 4 and len(reviews) == 2
    assert "Correct the example arithmetic" in requests[2]["messages"][-1]["content"]


def test_persistent_review_errors_never_publish_an_unchecked_lesson(monkeypatch):
    requests = []

    def provider(request):
        body = json.loads(request.content)
        requests.append(body)
        return model_response(
            {"approved": False, "issues": ["The explanation is still incorrect."]}
            if is_review(body)
            else example_storyboard().model_dump()
        )

    mock_provider(monkeypatch, provider)
    with pytest.raises(PipelineError, match="facts and visuals review"):
        plan_lesson("Explain the parabola through squaring", "beginner")
    assert len(requests) == 4


def test_failed_review_never_publishes_the_draft(monkeypatch):
    requests = []

    def provider(request):
        requests.append(request)
        return (
            model_response(example_storyboard().model_dump()) if len(requests) == 1 else httpx.Response(401)
        )

    mock_provider(monkeypatch, provider)
    with pytest.raises(PipelineError, match="API key"):
        plan_lesson("Explain the parabola through squaring", "beginner")


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


def test_provider_json_generation_failure_is_retried_before_review(monkeypatch):
    calls = []

    def provider(request):
        body = json.loads(request.content)
        calls.append(body)
        if len(calls) == 1:
            return httpx.Response(400, json={"error": {"code": "json_validate_failed"}})
        return model_response(
            {"approved": True, "issues": []} if is_review(body) else example_storyboard().model_dump()
        )

    mock_provider(monkeypatch, provider)
    assert plan_lesson("Explain the parabola through squaring", "beginner")[0].scenes
    assert len(calls) == 3
