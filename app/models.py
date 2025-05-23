from pydantic import BaseModel

class GenerateRequest(BaseModel):
    prompt: str
    chat_id: str

class GenerateResponse(BaseModel):
    video_url: str