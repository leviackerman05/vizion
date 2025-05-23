from pydantic import BaseModel
from typing import List, Optional

class GenerateRequest(BaseModel):
    user_id: str
    chat_id: str
    prompt: str

class GenerateResponse(BaseModel):
    video_url: str

class ChatSummary(BaseModel):
    chat_id: str
    createdAt: str
