import json
import logging
import time

import httpx
from pydantic import Field, ValidationError, model_validator

from vizion.prompts import PROMPT_VERSION, REVIEW_PROMPT, SYSTEM_PROMPT
from vizion.schema import Storyboard, StrictModel
from vizion.settings import settings


class PipelineError(Exception):
    """A safe, actionable message that may be shown in the UI."""


class ReviewVerdict(StrictModel):
    approved: bool
    issues: list[str] = Field(max_length=8)

    @model_validator(mode="after")
    def consistent_verdict(self):
        if self.approved == bool(self.issues):
            raise ValueError("Approved reviews have no issues; rejected reviews must explain the issues")
        return self


def plan_lesson(topic: str, audience: str, notify=lambda *_: None) -> tuple[Storyboard, str]:
    original = {"role": "user", "content": json.dumps({"topic": topic, "audience": audience})}
    draft, model = _validated_output(
        [{"role": "system", "content": SYSTEM_PROMPT}, original], notify, "draft"
    )
    for review_attempt in range(2):
        verdict, _ = _validated_output(
            [
                {"role": "system", "content": REVIEW_PROMPT},
                {
                    "role": "user",
                    "content": json.dumps(
                        {"topic": topic, "audience": audience, "storyboard": draft.model_dump()}
                    ),
                },
            ],
            notify,
            "final_review" if review_attempt else "review",
            ReviewVerdict,
        )
        if verdict.approved:
            return draft, f"{settings.llm_provider}:{model}:{PROMPT_VERSION}"
        if review_attempt == 0:
            draft, model = _validated_output(
                [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    original,
                    {"role": "assistant", "content": draft.model_dump_json()},
                    {
                        "role": "user",
                        "content": "Correct every specific review issue below. Preserve the topic and return the complete corrected lesson JSON. Issues: "
                        + json.dumps(verdict.issues),
                    },
                ],
                notify,
                "repair",
            )
    raise PipelineError(
        "This lesson did not pass its facts and visuals review. Try a narrower topic with a concrete example."
    )


def _validated_output(messages, notify, phase, output_type=Storyboard):
    provider = settings.llm_provider
    key = settings.groq_api_key if provider == "groq" else settings.gemini_api_key
    if not key:
        raise PipelineError(f"The {provider.title()} API key has not been configured for the lesson worker.")
    schema = output_type.model_json_schema()
    for attempt in range(3):
        base = {"draft": 10, "review": 30, "repair": 50, "final_review": 70}[phase]
        notify(
            base + attempt * 5,
            "Planning the explanation"
            if phase == "draft"
            else "Checking facts and matching narration to visuals",
        )
        try:
            with httpx.Client(timeout=httpx.Timeout(90, connect=10)) as client:
                if provider == "groq":
                    model = settings.groq_model
                    response = client.post(
                        "https://api.groq.com/openai/v1/chat/completions",
                        headers={"Authorization": f"Bearer {key}"},
                        json={
                            "model": model,
                            "messages": messages,
                            "temperature": 0.3 if phase == "draft" else 0,
                            "max_completion_tokens": 4000 if output_type is ReviewVerdict else 5500,
                            "reasoning_effort": "low" if phase == "draft" or attempt else "medium",
                            "response_format": {"type": "json_object"}
                            if output_type is ReviewVerdict
                            else {
                                "type": "json_schema",
                                "json_schema": {"name": "lesson", "strict": True, "schema": schema},
                            },
                        },
                    )
                else:
                    model = settings.gemini_model
                    # Topic and validation feedback remain untrusted user data.
                    response = client.post(
                        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                        headers={"x-goog-api-key": key},
                        json={
                            "systemInstruction": {"parts": [{"text": messages[0]["content"]}]},
                            "contents": [{"role": "user", "parts": [{"text": json.dumps(messages[1:])}]}],
                            "generationConfig": {
                                "responseMimeType": "application/json",
                                "responseJsonSchema": schema,
                            },
                        },
                    )
            if response.status_code == 429:
                if attempt < 2:
                    notify(base, "The free model API is busy. Waiting before retrying.")
                    try:
                        delay = min(30, max(2, float(response.headers.get("retry-after", 10))))
                    except ValueError:
                        delay = 10
                    time.sleep(delay)
                    continue
                raise PipelineError(
                    "The free model quota is temporarily exhausted. Try this project again later."
                )
            if response.status_code in (401, 403):
                raise PipelineError(
                    "The model provider rejected the API key. Check the worker's provider configuration."
                )
            if response.status_code == 400:
                error_code = response.json().get("error", {}).get("code")
                if error_code == "json_validate_failed" and attempt < 2:
                    messages.append(
                        {
                            "role": "user",
                            "content": "Your response failed the provider's JSON validation. Return only a complete JSON object matching the supplied schema, without commentary.",
                        }
                    )
                    continue
            if response.status_code >= 400:
                raise PipelineError(
                    f"The model provider could not plan this lesson (HTTP {response.status_code})."
                )
            payload = response.json()
            if provider == "groq":
                raw = payload["choices"][0]["message"].get("content") or ""
            else:
                raw = "".join(part.get("text", "") for part in payload["candidates"][0]["content"]["parts"])
            try:
                plan = output_type.model_validate_json(raw)
                return plan, model
            except ValidationError as exc:
                logging.getLogger(__name__).warning(
                    "Invalid model JSON phase=%s finish=%s completion_tokens=%s errors=%s",
                    phase,
                    (payload.get("choices") or [{}])[0].get("finish_reason"),
                    (payload.get("usage") or {}).get("completion_tokens"),
                    [error["type"] for error in exc.errors(include_input=False)],
                )
                # Never silently substitute an unrelated example after model failure.
                messages.extend(
                    [
                        {"role": "assistant", "content": raw[:14000]},
                        {
                            "role": "user",
                            "content": "Correct this JSON response. Validation failed: "
                            + str(exc.errors(include_input=False))[:2000]
                            + (
                                ". Return ONLY approved (boolean) and issues (string array). Do not return or rewrite the storyboard."
                                if output_type is ReviewVerdict
                                else ". Preserve the requested topic."
                            ),
                        },
                    ]
                )
        except (httpx.HTTPError, KeyError, IndexError, ValueError) as exc:
            if attempt == 2:
                raise PipelineError("The model returned an incomplete response. Retry this project.") from exc
    raise PipelineError(
        "The model did not return a valid review verdict. Your project is saved; retry it."
        if output_type is ReviewVerdict
        else "The lesson did not pass storyboard validation after three attempts. Try a narrower topic."
    )
