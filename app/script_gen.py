import os
import re
import ast
import requests
from pathlib import Path
from dotenv import load_dotenv
from typing import List, Optional

from app.prompt_engine.prompts import PROMPT_TEMPLATES
from app.models.schemas import ChatMessage
try:
    from app.prompt_engine.smart_intent_detector import detect_intent
    print("Using smart intent detector (embedding-based)")
except Exception:
    from app.prompt_engine.intent_detector import detect_intent
    print("Falling back to keyword-based intent detector")

from app.prompt_engine.script_validation import check_for_invalid_manim_methods

# Load environment variables
load_dotenv()

def extract_code_from_response(text: str) -> str:
    match = re.search(r"```(?:python)?\n(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()

    start_index = text.find("from manim import *")
    return text[start_index:].strip() if start_index != -1 else text.strip()


def generate_prompt_template(user_prompt: str) -> str:
    intent = detect_intent(user_prompt)
    template_fn = PROMPT_TEMPLATES.get(intent, PROMPT_TEMPLATES["concept_explanation"])
    return template_fn("").strip()


def generate_script(
    user_prompt: str,
    prevMessages: Optional[List[ChatMessage]] = None,
    latest_code: Optional[str] = None,
    model: str = "gemini-2.0-flash",
    output_path: str = "app/static/outputs/generated_scene.py"
) -> str:
    conversation_history = []  # Keeps track of prior prompts and responses

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError("\u274c GEMINI_API_KEY environment variable is not set.")

    # If history is empty, include the prompt template as system prompt
    if not conversation_history:
        system_prompt = generate_prompt_template(user_prompt)
        conversation_history.append({"role": "user", "content": system_prompt})

    if prevMessages:
        for msg in prevMessages:
            conversation_history.append({"role": "user", "content": msg['message']})

    # Load previous script if this is a new session
    if latest_code and os.path.exists(output_path):
        conversation_history.append({"role": "model", "content": latest_code})

    conversation_history.append({"role": "user", "content": user_prompt})

    # Build Gemini request payload with full conversation history
    contents = []
    for msg in conversation_history:
        contents.append({
            "role": msg["role"],
            "parts": [{"text": msg["content"]}]
        })

    payload = {"contents": contents}
    print(f"Payload: {payload}")
    print(f"\n Sending prompt to model: {model}")

    response = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}",
        headers={"Content-Type": "application/json"},
        json=payload
    )

    if response.status_code != 200:
        print(f" API request failed: {response.status_code}")
        print(response.text)
        return ""

    try:
        raw_output = response.json()["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError) as e:
        print(f" Failed to parse response: {e}")
        print(response.text)
        return ""

    script_code = extract_code_from_response(raw_output)

    if "Scene" not in script_code or "class" not in script_code:
        print(" Invalid response: Not a Manim script. Skipping save.")
        print(" Raw output:\n", raw_output)
        return ""

    invalids = check_for_invalid_manim_methods(script_code)
    if invalids:
        print(f" Warning: Detected hallucinated Manim methods: {', '.join(invalids)}")

    if "from manim import *" not in script_code:
        script_code = "from manim import *\n" + script_code

    try:
        script_code = re.sub(r"class\s+\w+\s*\(", "class GeneratedScene(", script_code)
        ast.parse(script_code)
    except SyntaxError as e:
        print(" Syntax error in generated code. Skipping save.")
        print(f" Error: {e}")
        print(" Raw output:\n", script_code)
        return ""

    Path(output_path).write_text(script_code, encoding="utf-8")
    print(f" Manim script saved to: {output_path}\n")

    # Add model response to history
    conversation_history.append({"role": "model", "content": script_code})

    return script_code
