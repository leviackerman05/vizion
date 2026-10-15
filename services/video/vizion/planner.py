import json
import time

import httpx
from pydantic import ValidationError

from vizion.prompts import PROMPT_VERSION, SYSTEM_PROMPT
from vizion.schema import Storyboard
from vizion.settings import settings


class PipelineError(Exception):
    """A safe, actionable message that may be shown in the UI."""


def plan_lesson(topic: str, audience: str, notify=lambda *_: None) -> tuple[Storyboard, str]:
    provider = settings.llm_provider
    key = settings.groq_api_key if provider == "groq" else settings.gemini_api_key
    if not key:
        raise PipelineError(f"The {provider.title()} API key has not been configured for the lesson worker.")
    schema = Storyboard.model_json_schema()
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": json.dumps({"topic": topic, "audience": audience})},
    ]
    for attempt in range(3):
        notify(10 + attempt * 5, "Planning the explanation and checking the storyboard")
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
                            "temperature": 0.3,
                            "max_completion_tokens": 5500,
                            "reasoning_effort": "low",
                            "response_format": {
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
                            "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
                            "contents": [{"role": "user", "parts": [{"text": json.dumps(messages[1:])}]}],
                            "generationConfig": {
                                "responseMimeType": "application/json",
                                "responseJsonSchema": schema,
                            },
                        },
                    )
            if response.status_code == 429:
                if attempt < 2:
                    notify(12, "The free model API is busy. Waiting before retrying.")
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
                plan = Storyboard.model_validate_json(raw)
                return plan, f"{provider}:{model}:{PROMPT_VERSION}"
            except ValidationError as exc:
                # Never silently substitute an unrelated example after model failure.
                messages.extend(
                    [
                        {"role": "assistant", "content": raw[:14000]},
                        {
                            "role": "user",
                            "content": "Correct this storyboard. Validation failed: "
                            + str(exc.errors(include_input=False))[:2000]
                            + ". Preserve the requested topic.",
                        },
                    ]
                )
        except (httpx.HTTPError, KeyError, IndexError, ValueError) as exc:
            if attempt == 2:
                raise PipelineError("The model returned an incomplete response. Retry this project.") from exc
    raise PipelineError(
        "The lesson did not pass storyboard validation after three attempts. Try a narrower topic."
    )
