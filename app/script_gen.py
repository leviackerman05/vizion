import ollama
import re
import ast
from pathlib import Path

def extract_code_from_response(text: str) -> str:
    """Extracts Python code from triple backtick blocks in the LLM's response."""
    clean_text = re.sub(r"```(?:python)?\n(.*?)```", r"\1", text, flags=re.DOTALL).strip()
    return clean_text

def generate_script(user_prompt: str, model: str = "llama3", output_path: str = "generated_scene.py") -> str:
    """
    Sends prompt to Ollama model and saves the extracted Manim code to a .py file.
    Ensures valid response format and Python syntax.
    """
    system_prompt = (
        "You are an extremely skilled and friendly software developer assistant who exists to generate Manim code. "
        "All your responses should be strictly Python code to generate animations in the Manim Community Edition. "
        "Avoid extra explanations or markdown formatting. Only respond with the main code.\n\n"
        "------\n"
        "RESPONSE FORMAT:\n"
        "Just respond with main code. No explanations or markdown.\n\n"
        "Key Guidelines:\n"
        "1. To create shapes, ensure the coordinates are correctly placed in 2D space (e.g., `[x, y, 0]` for vertices).\n"
        "2. Use the `Rectangle` class for rectangles (e.g., `Rectangle(width=2, height=1)`). Ensure you set the fill and opacity correctly.\n"
        "3. For arrows, use the `Arrow` class with `start` and `end` points. For transformations, use `Transform(from_shape, to_shape)`.\n"
        "4. For text, use the `Text` class (e.g., `Text('START')`). Position it inside shapes using `.move_to()` or `.shift()`. The text should be properly centered in the shape.\n"
        "5. Use `self.play(...)` for all animations and ensure smooth transitions.\n"
        "6. When transforming shapes, always use `Transform` or `animate` for smooth animations. Ensure that the objects transform in sync.\n"
        "7. Ensure proper use of `set_fill(color)` and `set_opacity(value)` to apply styles to shapes.\n"
        "8. All code must be valid and must import `from manim import *` at the top.\n\n"
        "Example 1: 'Draw a red circle and animate it color to blue'\n"
        "Output:\n"
        "from manim import *\n\n"
        "class RedToBlueCircle(Scene):\n"
        "    def construct(self):\n"
        "        # Create a red circle\n"
        "        circle = Circle(color=RED)\n"
        "        self.play(Create(circle))\n\n"
        "        # Animate the color change from red to blue\n"
        "        self.play(circle.animate.set_color(BLUE))\n\n"
        "        # Hold the final state for a second\n"
        "        self.wait(1)\n\n"
    )


    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    print(f"\n📤 Sending prompt to model: {model}")
    response = ollama.chat(model=model, messages=messages)
    raw_output = response["message"]["content"]

    script_code = extract_code_from_response(raw_output)

    if "Scene" not in script_code or "class" not in script_code:
        print("❌ Invalid response: Not a Manim script. Skipping save.")
        print("🧾 Raw output:\n", raw_output)
        return ""

    if "from manim import *" not in script_code:
        script_code = "from manim import *\n" + script_code

    try:
        # Try to find and replace class name if it doesn't match
        if "class GeneratedScene" not in script_code:
            script_code = script_code.replace("class MyScene", "class GeneratedScene")
        ast.parse(script_code)
    except SyntaxError as e:
        print("❌ Syntax error in generated code. Skipping save.")
        print(f"📄 Error: {e}")
        print("🧾 Raw output:\n", script_code)
        return ""

    Path(output_path).write_text(script_code)
    print(f"✅ Manim script saved to: {output_path}\n")

    return script_code
