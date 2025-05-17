from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.models import GenerateRequest, GenerateResponse
from app.script_gen import generate_script
from app.renderer import render_manim_script

import re
import subprocess

app = FastAPI()

# Allow any origin for now (you can restrict later)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (video outputs)
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.post("/generate", response_model=GenerateResponse)
def generate_animation(request: GenerateRequest):
    try:
        output_path = "app/static/outputs/generated_scene.py"
        generate_script(request.prompt, output_path=output_path)
        video_url = render_manim_script(output_path)
        return {"video_url": video_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# CLI entry point for testing without API
def cli_mode():
    prompt = input("Enter your prompt: ")
    output_path = "app/static/outputs/generated_scene.py"
    generate_script(prompt, output_path=output_path)

    with open(output_path, "r", encoding="utf-8") as f:
        script_content = f.read()

    class_name_match = re.search(r'class\s+(\w+)', script_content)
    class_name = class_name_match.group(1) if class_name_match else "GeneratedScene"
    print(f"Detected scene class: {class_name}")

    subprocess.run([
        "manim",
        "-pql",
        output_path,
        class_name,
        "--media_dir", "app/static/outputs"
    ])


# This triggers only when you run `python app/main.py`
if __name__ == "__main__":
    cli_mode()
