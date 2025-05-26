from pydantic import BaseModel
from typing import List

class GenerateRequest(BaseModel):
    user_id: str
    chat_id: str
    prompt: str

class GenerateResponse(BaseModel):
    video_url: str

class ChatSummary(BaseModel):
    chat_id: str
    createdAt: str
    name: str

class ChatMessage(BaseModel):
    message: str
    timestamp: str

class ChatData(BaseModel):
    messages: List[ChatMessage]
    latest_code: str
