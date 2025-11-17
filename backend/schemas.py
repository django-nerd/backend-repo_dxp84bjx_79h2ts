from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Literal, List

class User(BaseModel):
    email: EmailStr
    password_hash: str
    credits: int = 50

class AuthSignup(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)

class AuthLogin(BaseModel):
    email: EmailStr
    password: str

ToolName = Literal[
    "styling", "room", "avatar", "meme", "bgremove"
]

class GenerationRequest(BaseModel):
    tool: ToolName
    prompt: Optional[str] = None
    options: Optional[dict] = None

class GalleryItem(BaseModel):
    user_id: str
    tool: ToolName
    image_url: str
    meta: Optional[dict] = None
