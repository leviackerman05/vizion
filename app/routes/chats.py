from fastapi import APIRouter, HTTPException, Request
from typing import List
from pathlib import Path
from app.models.schemas import ChatSummary, GenerateRequest, GenerateResponse
from app.firebase.chat_service import (
    get_user_chats,
    add_message,
    get_chat_messages,
    update_latest_code
)
from app.script_gen import generate_script
from app.renderer import render_manim_script

router = APIRouter()


@router.get("/chats/{user_id}", response_model=List[ChatSummary])
def fetch_user_chats(user_id: str):
    return get_user_chats(user_id)


@router.post("/chat")
def generate_and_render(req: GenerateRequest, request: Request):
    output_script_path = f"app/static/outputs/generated_{req.chat_id}.py"

    # Save user prompt
    add_message(req.user_id, req.chat_id, req.prompt)

    chatData = get_chat_messages(req.user_id, req.chat_id)
    messages = chatData.get("messages") if isinstance(chatData, dict) else None
    latest_code_list = chatData.get("latest_code") if isinstance(chatData, dict) else None
    latest_code = latest_code_list[0] if isinstance(latest_code_list, list) and latest_code_list else None

    try:
        generated_code = generate_script(
            user_prompt=req.prompt,
            prevMessages=messages,
            latest_code=latest_code,
            output_path=output_script_path
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Script generation failed: {str(e)}")

    try:
        video_url = render_manim_script(output_script_path, chat_id=req.chat_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Video rendering failed: {str(e)}")

    update_latest_code(req.user_id, req.chat_id, generated_code)
    full_url = f"{request.base_url}{video_url.lstrip('/')}"
    return GenerateResponse(video_url=full_url)


@router.get("/chatdata/{user_id}/{chat_id}")
def fetch_chat_messages_only(user_id: str, chat_id: str):
    data = get_chat_messages(user_id, chat_id)
    if not data or not data.get("messages"):
        raise HTTPException(status_code=404, detail="Chat not found")
    return { "messages": data["messages"] }



@router.get("/video/{user_id}/{chat_id}")
def fetch_video_from_latest_code(user_id: str, chat_id: str, request: Request):
    data = get_chat_messages(user_id, chat_id)
    if not data:
        raise HTTPException(status_code=404, detail="Chat not found")

    latest_code_list = data.get("latest_code")
    if not latest_code_list or not isinstance(latest_code_list, list):
        raise HTTPException(status_code=404, detail="No latest_code available")

    script_code = latest_code_list[0]
    output_script_path = f"app/static/outputs/generated_{chat_id}.py"
    Path(output_script_path).write_text(script_code, encoding="utf-8")

    try:
        video_url = render_manim_script(output_script_path, chat_id=chat_id)
        full_url = f"{request.base_url}{video_url.lstrip('/')}"
    except Exception as e:
        print("Video rendering failed:", str(e))
        raise HTTPException(status_code=500, detail="Video rendering failed")

    return { "videoUrl": full_url }

