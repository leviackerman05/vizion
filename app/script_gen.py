import os
import re
import ast
from pathlib import Path
from dotenv import load_dotenv
from typing import List, Optional

from openai import OpenAI

from app.prompt_engine.prompts import PROMPT_TEMPLATES
from app.models.schemas import ChatMessage

try:
    from app.prompt_engine.smart_intent_detector import detect_intent
    print("Using smart intent detector (embedding-based)")
except Exception:
    from app.prompt_engine.intent_detector import detect_intent
    print("Falling back to keyword-based intent detector")

from app.prompt_engine.script_validation import check_for_invalid_manim_methods

load_dotenv()

client = OpenAI(
    api_key=os.getenv("GEMINI_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

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
    conversation_history = []

    if not os.getenv("GEMINI_API_KEY"):
        raise EnvironmentError("❌ GEMINI_API_KEY not set in .env file")

    # Add system prompt based on intent
    system_prompt = generate_prompt_template(user_prompt)
    conversation_history.append({"role": "system", "content": system_prompt})

    if prevMessages:
        for msg in prevMessages:
            conversation_history.append({"role": "user", "content": msg['message']})

    if latest_code:
        conversation_history.append({"role": "assistant", "content": latest_code})

    conversation_history.append({"role": "user", "content": user_prompt})

    try:
        print("🧠 Sending to Gemini via OpenAI-compatible client...")
        response = client.chat.completions.create(
            model=model,
            messages=conversation_history
        )
        raw_output = response.choices[0].message.content
    except Exception as e:
        print("❌ Gemini API call failed:", e)
        return ""

    script_code = extract_code_from_response(raw_output)

    if "Scene" not in script_code or "class" not in script_code:
        print("❌ Not a valid Manim script.")
        print("Raw output:\n", raw_output)
        return ""

    invalids = check_for_invalid_manim_methods(script_code)
    if invalids:
        print(f"⚠️ Warning: Hallucinated Manim methods: {', '.join(invalids)}")

    if "from manim import *" not in script_code:
        script_code = "from manim import *\n" + script_code

    try:
        script_code = re.sub(r"class\s+\w+\s*\(", "class GeneratedScene(", script_code)
        ast.parse(script_code)
    except SyntaxError as e:
        print("❌ Syntax error in generated code.")
        print("Error:", e)
        print("Raw output:\n", script_code)
        return ""

    Path(output_path).write_text(script_code, encoding="utf-8")
    print(f"✅ Script saved to {output_path}")

    return script_code
