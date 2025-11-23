from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.models import GenerateRequest, GenerateResponse, SignupRequest, LoginRequest, AuthResponse, ChatRequest, ChatResponse
from app.script_gen import generate_script
from app.renderer import render_manim_script
from app.supabase_client import supabase
from app.auth import verify_token
from app.chat_service import create_chat, add_message, get_chat_history, get_user_chats, delete_chat, check_chat_exists
from app.auth import verify_token

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


@app.post("/signup", response_model=AuthResponse)
def signup(request: SignupRequest):
    """Register a new user with Supabase"""
    try:
        response = supabase.auth.sign_up({
            "email": request.email,
            "password": request.password,
            "options": {
                "data": {
                    "username": request.username
                }
            }
        })
        
        if response.user is None:
            raise HTTPException(status_code=400, detail="Signup failed")
        
        # Return empty token to force user to login (don't auto-authenticate)
        return {
            "access_token": "",
            "token_type": "bearer",
            "user": {
                "id": response.user.id,
                "email": response.user.email,
                "username": response.user.user_metadata.get("username")
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))



@app.post("/login", response_model=AuthResponse)
def login(request: LoginRequest):
    """Login with email and password"""
    print(f"Attempting login for: {request.email}")
    try:
        response = supabase.auth.sign_in_with_password({
            "email": request.email,
            "password": request.password
        })
        
        if response.user is None:
            print("Login failed: response.user is None")
            raise HTTPException(status_code=401, detail="Invalid credentials")
            
        print("Login successful")
        return {
            "access_token": response.session.access_token,
            "token_type": "bearer",
            "user": {
                "id": response.user.id,
                "email": response.user.email,
                "username": response.user.user_metadata.get("username")
            }
        }
    except Exception as e:
        print(f"Login error: {str(e)}")
        raise HTTPException(status_code=401, detail=str(e))



@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest, user: dict = Depends(verify_token)):
    """
    Handle chat messages. 
    - Creates a new chat if chat_id is missing OR if the provided chat_id doesn't exist.
    - Generates video for the prompt.
    - Saves user message and assistant response to DB.
    """
    try:
        user_id = user["sub"]
        chat_id = request.chat_id
        prompt = request.prompt
        
        # 1. Create chat if it doesn't exist
        if not chat_id:
            # Case A: No chat_id provided -> Create new chat
            title = (prompt[:30] + '...') if len(prompt) > 30 else prompt
            chat_id = create_chat(user_id, title)
        else:
            # Case B: chat_id provided -> Check if exists, if not create it with that ID
            if not check_chat_exists(chat_id):
                title = (prompt[:30] + '...') if len(prompt) > 30 else prompt
                chat_id = create_chat(user_id, title, chat_id=chat_id)
            
        # 2. Save User Message
        add_message(chat_id, "user", prompt)
        
        # 3. Generate Video
        output_path = "app/static/outputs/generated_scene.py"
        generate_script(prompt, output_path=output_path)
        video_url = render_manim_script(output_path)
        
        # 4. Save Assistant Message
        add_message(chat_id, "assistant", "Here is your video!", video_url)
        
        return {
            "chat_id": chat_id,
            "message": {
                "role": "assistant",
                "content": "Here is your video!",
                "video_url": video_url
            }
        }
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/chats")
def list_chats(user: dict = Depends(verify_token)):
    """List all chats for the authenticated user"""
    try:
        user_id = user["sub"]
        return get_user_chats(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/chatdata/{chat_id}")
def get_chat_data(chat_id: str, user: dict = Depends(verify_token)):
    """Get full history for a specific chat"""
    try:
        # Ideally check if user owns the chat first
        return get_chat_history(chat_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/chats/{chat_id}")
def get_chat_by_id(chat_id: str, user: dict = Depends(verify_token)):
    """Alias for /chatdata/{chat_id} to support frontend"""
    return get_chat_data(chat_id, user)



@app.delete("/chats/{chat_id}")
def delete_chat_endpoint(chat_id: str, user: dict = Depends(verify_token)):
    """Delete a chat"""
    try:
        delete_chat(chat_id)
        return {"status": "success"}
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
        "-pqh",
        output_path,
        class_name,
        "--media_dir", "app/static/outputs"
    ])


# This triggers only when you run `python app/main.py`
if __name__ == "__main__":
    cli_mode()
