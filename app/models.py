from pydantic import BaseModel, EmailStr

class GenerateRequest(BaseModel):
    prompt: str

class GenerateResponse(BaseModel):
    video_url: str

class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    username: str

class LoginRequest(BaseModel):

    email: EmailStr
    password: str

class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

class Message(BaseModel):
    role: str
    content: str
    video_url: str = None

class ChatRequest(BaseModel):
    prompt: str
    chat_id: str = None  # Optional: if None, creates a new chat
    user_id: str = None # Optional: ignored in favor of token


class ChatResponse(BaseModel):
    chat_id: str
    message: Message