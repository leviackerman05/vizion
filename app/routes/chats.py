from fastapi import APIRouter, HTTPException, Request
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
def generate_and_render(req: GenerateRequest, request: Request):
    # Clean chat_id to use in filename safely
    chat_id = re.sub(r'\W+', '', req.chat_id)
    output_script_path = f"app/static/outputs/generated_{chat_id}.py"

    # Step 1: Save user prompt message
    add_message(req.user_id, req.chat_id, req.prompt)

    chatData = get_chat_messages(req.user_id, chat_id)

    # Step 2: Generate code from LLM
    try:
        print("Raw chatData:", chatData)

        messages = chatData.get('messages') if isinstance(chatData, dict) else None
        print("Extracted messages:", messages)

        latest_code_list = chatData.get('latestCode') if isinstance(chatData, dict) else None
        print("Extracted latest_code_list:", latest_code_list)

        # Fallbacks in case of missing data
        if not isinstance(messages, list):
            print("messages is not a list, setting to None")
            messages = None

        if isinstance(latest_code_list, list) and latest_code_list:
            latest_code = latest_code_list[0]
            print("latest_code set from list:", latest_code)
        else:
            latest_code = None  # or "" depending on your app logic
            print("latest_code not present or not a list, setting to None")

        print("Calling generate_script with:")
        print("  user_prompt:", req.prompt)
        print("  prevMessages:", messages)
        print("  latest_code:", latest_code)
        print("  output_path:", output_script_path)

        generated_code = generate_script(
            user_prompt=req.prompt,
            prevMessages=messages,
            latest_code=latest_code,
            output_path=output_script_path
        )
    except Exception as e:
        print("Error during script generation:", str(e))
        raise HTTPException(status_code=500, detail=f"Script generation failed: {str(e)}")

    # Step 3: Try to render the video
    try:
        video_url = render_manim_script(output_script_path, chat_id=chat_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Video rendering failed: {str(e)}")

    # Optional: store latest code + URL in Firestore
    update_latest_code(req.user_id, req.chat_id, generated_code)

    # 🔥 Convert relative video path to full URL for frontend
    full_url = f"{request.base_url}{video_url.lstrip('/')}"
    return GenerateResponse(video_url=full_url)

@router.get("/chatdata/{user_id}/{chat_id}")
def fetch_chat(user_id: str, chat_id: str):
    data = get_chat_messages(user_id, chat_id)
    if not data:
        raise HTTPException(status_code=404, detail="Chat not found")
    return {"messages": data["messages"], "videoUrl": ""}
