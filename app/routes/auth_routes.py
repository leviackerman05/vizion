from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
import httpx
import os
import uuid
from datetime import datetime, timedelta
from dotenv import load_dotenv
from firebase_admin import firestore
from typing import List

load_dotenv()
FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY")
SESSION_EXPIRY_DAYS = 7

router = APIRouter()

class AuthRequest(BaseModel):
    email: str
    password: str

@router.post("/signup")
async def signup_user(data: AuthRequest):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FIREBASE_API_KEY}"
    payload = {
        "email": data.email,
        "password": data.password,
        "returnSecureToken": True,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)

    if response.status_code != 200:
        raise HTTPException(
            status_code=400,
            detail=response.json().get("error", {}).get("message", "Signup failed")
        )

    resp_data = response.json()
    return {
        "idToken": resp_data["idToken"],
        "uid": resp_data["localId"],
        "email": resp_data["email"],
    }

@router.post("/login")
async def login_user(data: AuthRequest, request: Request):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
    payload = {
        "email": data.email,
        "password": data.password,
        "returnSecureToken": True,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)

    if response.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    resp_data = response.json()
    uid = resp_data["localId"]
    session_id = str(uuid.uuid4())

    db = firestore.client()
    db.collection("users").document(uid).collection("sessions").document(session_id).set({
        "loginAt": datetime.utcnow(),
        "ip": request.client.host,
        "userAgent": request.headers.get("user-agent"),
        "active": True,
    })

    return {
        "idToken": resp_data["idToken"],
        "uid": uid,
        "email": resp_data["email"],
    }

@router.get("/sessions/{uid}")
def get_user_sessions(uid: str):
    db = firestore.client()
    session_docs = db.collection("users").document(uid).collection("sessions").stream()
    now = datetime.utcnow()
    sessions = []

    for doc in session_docs:
        data = doc.to_dict()
        login_time = data.get("loginAt")

        if not login_time:
            continue

        if data.get("active") and (now - login_time).days <= SESSION_EXPIRY_DAYS:
            sessions.append({**data, "sessionId": doc.id})

    return {"sessions": sessions}

@router.patch("/sessions/{uid}/{session_id}/revoke")
def revoke_session(uid: str, session_id: str):
    db = firestore.client()
    session_ref = db.collection("users").document(uid).collection("sessions").document(session_id)
    session_ref.update({"active": False})
    return {"status": "revoked", "sessionId": session_id}
