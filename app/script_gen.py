import os
import re
import ast
import requests
from pathlib import Path
from dotenv import load_dotenv

from app.prompt_engine.prompts import PROMPT_TEMPLATES
try:
    from app.prompt_engine.smart_intent_detector import detect_intent
    print("Using smart intent detector (embedding-based)")
except Exception:
    from app.prompt_engine.intent_detector import detect_intent
    print("Falling back to keyword-based intent detector")

from app.prompt_engine.script_validation import check_for_invalid_manim_methods

# NEW: Import template engine
from app.template_engine import generate_from_template

# Load environment variables
load_dotenv()

def extract_code_from_response(text: str) -> str:
    match = re.search(r"```(?:python)?\n(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()

    start_index = text.find("from manim import *")
    return text[start_index:].strip() if start_index != -1 else text.strip()

def generate_prompt_parts(user_prompt: str) -> list:
    intent = detect_intent(user_prompt)
    template = PROMPT_TEMPLATES.get(intent, PROMPT_TEMPLATES["concept_explanation"])
    parts = [
        {"text": template("").strip()},
        {"text": user_prompt.strip()}
    ]
    return [{"parts": parts}]

def generate_script_with_raw_llm(user_prompt: str, model: str, output_path: str) -> str:
    """
    Original code generation approach - generates raw code using LLM prompts.
    Used as fallback when template system doesn't match.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError("❌ GEMINI_API_KEY environment variable is not set.")

    payload = {"contents": generate_prompt_parts(user_prompt)}
    print(f"\n⚠️  Using fallback raw generation mode")
    print(f" Sending prompt to model: {model}")

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

    return script_code


def generate_script(user_prompt: str, model: str = "gemini-2.0-flash", output_path: str = "app/static/outputs/generated_scene.py") -> str:
    """
    Main script generation function.
    
    NEW BEHAVIOR:
    1. Try template system first (guaranteed layout)
    2. Fall back to raw LLM generation if no template matches
    """
    
    # Step 1: Try template system
    print("\n🎯 Attempting template-based generation...")
    script_code, status = generate_from_template(user_prompt)
    
    if script_code:
        print("✅ Template generation successful!")
    else:
        print(f"❌ Template generation failed: {status}")
        print("🔄 Falling back to raw LLM generation...")
        script_code = generate_script_with_raw_llm(user_prompt, model, output_path)
        
        if not script_code:
            print("❌ Raw generation also failed")
            return ""
    
    # Save the generated script
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(script_code, encoding="utf-8")
    print(f" Manim script saved to: {output_path}\n")

    return script_code