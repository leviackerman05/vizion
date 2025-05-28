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
    expiry = datetime.utcnow() + timedelta(days=SESSION_EXPIRY_DAYS)

    db = firestore.client()
    db.collection("users").document(uid).collection("sessions").document(session_id).set({
        "loginAt": datetime.utcnow(),
        "expiresAt": expiry,
        "ip": request.client.host,
        "userAgent": request.headers.get("user-agent"),
        "active": True,
    })

    return {
        "idToken": resp_data["idToken"],
        "uid": uid,
        "email": resp_data["email"],
        "sessionId": session_id,
    }

@router.post("/logout")
async def logout_user(request: Request):
    uid = request.headers.get("x-uid")
    session_id = request.headers.get("x-session-id")

    if not uid or not session_id:
        raise HTTPException(status_code=400, detail="Missing session headers")

    db = firestore.client()
    session_ref = db.collection("users").document(uid).collection("sessions").document(session_id)
    session_doc = session_ref.get()

    if not session_doc.exists:
        raise HTTPException(status_code=404, detail="Session not found")

    session_ref.update({"active": False, "logoutAt": datetime.utcnow()})
    return {"status": "success", "message": "Session deactivated"}

@router.get("/sessions/{uid}")
def get_user_sessions(uid: str):
    db = firestore.client()
    session_docs = db.collection("users").document(uid).collection("sessions").stream()
    now = datetime.utcnow()
    sessions = []

    for doc in session_docs:
        data = doc.to_dict()
        login_time = data.get("loginAt")
        expiry_time = data.get("expiresAt")

        if not login_time or not expiry_time:
            continue

        # Auto-deactivate expired sessions
        if datetime.utcnow() > expiry_time:
            db.collection("users").document(uid).collection("sessions").document(doc.id).update({"active": False})
            continue

        if data.get("active"):
            sessions.append({**data, "sessionId": doc.id})

    return {"sessions": sessions}

@router.patch("/sessions/{uid}/{session_id}/revoke")
def revoke_session(uid: str, session_id: str):
    db = firestore.client()
    session_ref = db.collection("users").document(uid).collection("sessions").document(session_id)
    session_ref.update({"active": False})
    return {"status": "revoked", "sessionId": session_id}
