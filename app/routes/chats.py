from fastapi import APIRouter, HTTPException
from app.models.schemas import ChatSummary
from app.firebase.chat_service import *
from fastapi import APIRouter, HTTPException
from app.models.schemas import GenerateRequest, GenerateResponse
from app.script_gen import generate_script
from app.renderer import render_manim_script
from app.firebase.chat_service import add_message, update_latest_code
import re

router = APIRouter()

@router.get("/chats/{user_id}", response_model=List[ChatSummary])
def fetch_user_chats(user_id: str):
    return get_user_chats(user_id)

@router.post("/chat")
def generate_and_render(req: GenerateRequest):
    # Step 1: Save user prompt message
    add_message(req.user_id, req.chat_id, req.prompt)

    # Clean chat_id to use in filename safely
    chat_id = re.sub(r'\W+', '', req.chat_id)
    output_script_path = f"app/static/outputs/generated_{chat_id}.py"

    # Step 2: Generate code from LLM
    try:
        generated_code = generate_script(req.prompt, output_path=output_script_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Script generation failed: {str(e)}")

    # Step 3: Try to render the video
    try:
        video_url = render_manim_script(output_script_path, chat_id=chat_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Video rendering failed: {str(e)}")

    update_latest_code(req.user_id, req.chat_id, generated_code)

    return GenerateResponse(video_url=video_url)

@router.get("/chats/{user_id}/{chat_id}")
def fetch_chat(user_id: str, chat_id: str):
    data = get_chat_messages(user_id, chat_id)
    if not data:
        raise HTTPException(status_code=404, detail="Chat not found")
    latest_code = get_latest_code(user_id)
    return {"messages": data["messages"], "latestCode": latest_code}
