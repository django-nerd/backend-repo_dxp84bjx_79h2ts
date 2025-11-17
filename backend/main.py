from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime, timedelta
from passlib.hash import bcrypt
import jwt
import os

from schemas import AuthSignup, AuthLogin, GenerationRequest, GalleryItem, ToolName
from database import db, create_document, get_documents

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = 60 * 24 * 7

app = FastAPI(title="StudioAljo API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_user_collection():
    return db["user"]


def get_gallery_collection():
    return db["galleryitem"]


@app.get("/test")
async def test():
    # verify db connection by listing collections
    try:
        _ = db.list_collection_names()
        return {"ok": True, "service": "StudioAljo API"}
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@app.post("/auth/signup", response_model=TokenResponse)
async def signup(payload: AuthSignup):
    users = get_user_collection()
    if users.find_one({"email": payload.email}):
        raise HTTPException(400, detail="Email already registered")
    password_hash = bcrypt.hash(payload.password)
    create_document("user", {"email": payload.email, "password_hash": password_hash, "credits": 50})
    token = create_access_token({"sub": payload.email})
    return TokenResponse(access_token=token)


@app.post("/auth/login", response_model=TokenResponse)
async def login(payload: AuthLogin):
    users = get_user_collection()
    user = users.find_one({"email": payload.email})
    if not user or not bcrypt.verify(payload.password, user.get("password_hash", "")):
        raise HTTPException(401, detail="Invalid credentials")
    token = create_access_token({"sub": payload.email})
    return TokenResponse(access_token=token)


@app.get("/quota")
async def quota(email: str):
    users = get_user_collection()
    user = users.find_one({"email": email})
    if not user:
        raise HTTPException(404, detail="User not found")
    return {"credits": user.get("credits", 0), "limit": 50}


@app.post("/generate")
async def generate(tool: ToolName = Form(...), email: str = Form(...), options: Optional[str] = Form(None), file: UploadFile = File(...)):
    # This is a stub that simulates generation and decrements quota.
    users = get_user_collection()
    user = users.find_one({"email": email})
    if not user:
        raise HTTPException(404, detail="User not found")
    credits = int(user.get("credits", 0))
    if credits <= 0:
        raise HTTPException(402, detail="Out of credits")

    # In real world, call model here; we just pretend and return a placeholder image URL
    users.update_one({"_id": user["_id"]}, {"$inc": {"credits": -1}})
    fake_url = "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?q=80&w=1200&auto=format&fit=crop"
    return {"image_url": fake_url, "tool": tool}


@app.post("/gallery")
async def save_to_gallery(item: GalleryItem):
    _id = create_document("galleryitem", item.model_dump())
    return {"id": _id}


@app.get("/gallery")
async def get_gallery(email: str, limit: int = 50):
    items = get_documents("galleryitem", {"user_id": email}, limit)
    return {"items": items}


@app.delete("/gallery")
async def delete_gallery_item(id: str):
    res = db["galleryitem"].delete_one({"_id": id})
    if res.deleted_count == 0:
        raise HTTPException(404, detail="Not found")
    return {"ok": True}
