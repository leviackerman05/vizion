from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.models import GenerateRequest, GenerateResponse
from app.script_gen import generate_script
from app.renderer import render_manim_script

import re
import logging

app = FastAPI()

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files like rendered videos
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Enable logging for better debugging
logging.basicConfig(level=logging.INFO)

@app.post("/generate", response_model=GenerateResponse)
def generate_animation(request_data: GenerateRequest, request: Request):
    try:
        # Clean chat_id to use in filename safely
        chat_id = re.sub(r'\W+', '', request_data.chat_id)
        output_script_path = f"app/static/outputs/generated_{chat_id}.py"

        logging.info(f"[Prompt] {request_data.prompt}")
        logging.info(f"[Chat ID] {chat_id}")
        logging.info(f"[Script Path] {output_script_path}")

        # Generate script
        generate_script(request_data.prompt, output_path=output_script_path)

        # Render animation and get relative video path
        video_url = render_manim_script(output_script_path, chat_id=chat_id)

        # Build full URL for frontend access
        full_url = f"{request.base_url}{video_url.lstrip('/')}"
        return {"video_url": full_url}

    except Exception as e:
        logging.exception("[ERROR] Failed to generate video")
        raise HTTPException(status_code=500, detail=str(e))

# CLI-only mode for local testing without API
def cli_mode():
    prompt = input("Enter your prompt: ")
    chat_id = re.sub(r'\W+', '', input("Enter chat ID: "))
    output_path = f"app/static/outputs/generated_{chat_id}.py"

    generate_script(prompt, output_path=output_path)

    with open(output_path, "r", encoding="utf-8") as f:
        script_content = f.read()

    class_name_match = re.search(r'class\s+(\w+)', script_content)
    class_name = class_name_match.group(1) if class_name_match else "GeneratedScene"

    subprocess.run([
        "manim",
        "-pqh",
        output_path,
        class_name,
        "--media_dir", f"app/static/outputs/videos/generated_{chat_id}"
    ])

if __name__ == "__main__":
    cli_mode()
