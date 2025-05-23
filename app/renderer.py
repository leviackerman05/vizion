import os
import subprocess
import re
from pathlib import Path

def camel_to_snake(name: str) -> str:
    """Converts CamelCase to snake_case"""
    s1 = re.sub(r'(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

def render_manim_script(script_path: str, chat_id: str, class_name: str = "GeneratedScene") -> str:
    # Define output directory per chat
    output_dir = f"app/static/outputs/videos/generated_{chat_id}"
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Build command
    command = [
        "manim",
        "-pqh",
        script_path,
        class_name,
        "--media_dir", output_dir,
        "--output_file", "scene.mp4"
    ]

    subprocess.run(command, check=True)

    # Return the URL path to the rendered video
    return f"/static/outputs/videos/generated_{chat_id}/480p15/scene.mp4"
