import os
import subprocess
import re
from pathlib import Path

def camel_to_snake(name: str) -> str:
    """Converts CamelCase to snake_case"""
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

def render_manim_script(script_path: str, chat_id: str, class_name: str = "GeneratedScene") -> str:
    # Use shared output base dir, let Manim handle subfolders
    base_media_dir = "app/static/outputs"
    Path(base_media_dir).mkdir(parents=True, exist_ok=True)

    # Run the Manim render command
    command = [
        "manim",
        "-ql",
        "-o", "scene.mp4",
        "--media_dir", base_media_dir,
        script_path,
        class_name
    ]
    subprocess.run(command, check=True)

    # Return the URL path to the rendered video
    return f"/static/outputs/videos/generated_{chat_id}/480p15/scene.mp4"