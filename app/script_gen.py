import requests
import re
import ast
import os
from pathlib import Path
from dotenv import load_dotenv


load_dotenv()

def extract_code_from_response(text: str) -> str:
    """Extracts Python code from triple backtick blocks."""
    clean_text = re.sub(r"```(?:python)?\n(.*?)```", r"\1", text, flags=re.DOTALL).strip()
    return clean_text

def generate_script(user_prompt: str, model: str = "gemini-2.0-flash", output_path: str = "generated_scene.py") -> str:
    """
    Sends prompt to Gemini API and saves the extracted Manim code to a .py file.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError("❌ GEMINI_API_KEY environment variable is not set.")

    system_prompt = (
        "You are an extremely skilled and friendly software developer assistant who exists to generate Manim code. "
        "All your responses should be strictly Python code to generate animations in the Manim Community Edition. "
        "Avoid extra explanations or markdown formatting. Only respond with the main code.\n\n"
        "------\n"
        "RESPONSE FORMAT:\n"
        "Just respond with main code. No explanations or markdown.\n\n"
        "Key Guidelines:\n"
        "1. Use `from manim import *` at the top.\n"
        "2. Define a class that inherits from `Scene`.\n"
        "3. Use valid Manim syntax and animations.\n"
        "4. Do not return any markdown or explanations.\n"
    )

    payload = {
        "contents": [{
            "parts": [{
                "text": f"{system_prompt}\n\nUser Prompt: {user_prompt}"
            }]
        }]
    }

    print(f"\n📤 Sending prompt to model: {model}")
    response = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}",
        headers={"Content-Type": "application/json"},
        json=payload
    )

    if response.status_code != 200:
        print(f"❌ API request failed: {response.status_code}")
        print(response.text)
        return ""

    try:
        raw_output = response.json()["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError) as e:
        print(f"❌ Failed to parse response: {e}")
        print(response.text)
        return ""

    script_code = extract_code_from_response(raw_output)

    if "Scene" not in script_code or "class" not in script_code:
        print("❌ Invalid response: Not a Manim script. Skipping save.")
        print("🧾 Raw output:\n", raw_output)
        return ""

    if "from manim import *" not in script_code:
        script_code = "from manim import *\n" + script_code

    try:
        # Try to find and replace class name if needed
        if "class GeneratedScene" not in script_code:
            script_code = script_code.replace("class MyScene", "class GeneratedScene")
        ast.parse(script_code)
    except SyntaxError as e:
        print("❌ Syntax error in generated code. Skipping save.")
        print(f"📄 Error: {e}")
        print("🧾 Raw output:\n", script_code)
        return ""

    Path(output_path).write_text(script_code, encoding="utf-8")
    print(f"✅ Manim script saved to: {output_path}\n")

    return script_code
