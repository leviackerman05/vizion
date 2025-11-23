import os
import subprocess
import re

def camel_to_snake(name: str) -> str:
    """Converts CamelCase to snake_case"""
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

def render_manim_script(script_path: str, class_name: str = "GeneratedScene") -> str:
    output_dir = "app/static/outputs"
    
    # Path used by Manim internally (don't modify)
    manim_output_subpath = f"videos/{class_name}/480p15/scene.mp4"
    manim_output_path = os.path.join(output_dir, manim_output_subpath)

    # Use the exact class name for the URL path to match Manim's output directory
    url_path = f"/static/outputs/videos/{class_name}/480p15/scene.mp4"

    # Run the Manim render command
    command = [
        "manim",
        "-pqh",
        script_path,
        class_name,
        "--media_dir", output_dir,
        "--output_file", "scene.mp4"
    ]
    subprocess.run(command, check=True)

    return url_path
