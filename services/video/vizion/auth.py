"""Argon2 passwords and revocable, server-side sessions in HttpOnly cookies."""

import hashlib
import secrets
import time

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pwdlib import PasswordHash
from pydantic import EmailStr, Field
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError

from vizion.db import AuthAttempt, LoginSession, User, transaction
from vizion.schema import StrictModel
from vizion.settings import settings

router = APIRouter(prefix="/api/auth", tags=["Authentication"])
hasher = PasswordHash.recommended()
DUMMY_HASH = hasher.hash("Timing equalization for unknown users")


def digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def guard_origin(request: Request):
    if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        if request.headers.get("x-vizion-client") != "web":
            raise HTTPException(403, "Missing request verification header")
        origin = request.headers.get("origin")
        allowed = {settings.public_url.rstrip("/")}
        if not settings.production:
            allowed.update(
                {
                    "http://localhost:8080",
                    "http://127.0.0.1:8080",
                    "http://127.0.0.1:8000",
                    "http://localhost:8000",
                }
            )
        if origin and origin.rstrip("/") not in allowed:
            raise HTTPException(403, "Request origin is not allowed")
    if request.headers.get("sec-fetch-site") == "cross-site":
        raise HTTPException(403, "Cross-site requests are not allowed")


def check_attempts(request: Request, email: str, action: str = "login"):
    # Railway provides the real client address in X-Forwarded-For; keep its final trusted hop.
    address = request.headers.get("x-forwarded-for", "").split(",")[-1].strip() or (
        request.client.host if request.client else "unknown"
    )
    now = time.time()
    with transaction() as db:
        db.execute(delete(AuthAttempt).where(AuthAttempt.created_at < now - 86400))
        for scope, limit, window in (
            (f"{action}:email:{email}", 12, 900),
            (f"{action}:ip:{address}", 40 if action == "login" else 12, 3600),
        ):
            bucket = digest(scope)
            count = db.scalar(
                select(func.count())
                .select_from(AuthAttempt)
                .where(AuthAttempt.bucket == bucket, AuthAttempt.created_at > now - window)
            )
            if count >= limit:
                raise HTTPException(
                    429, "Too many attempts. Try again later.", headers={"Retry-After": "900"}
                )
            db.add(AuthAttempt(bucket=bucket))


def set_cookie(response: Response, token: str):
    response.set_cookie(
        settings.cookie_name,
        token,
        httponly=True,
        secure=settings.production,
        samesite="lax",
        max_age=settings.session_days * 86400,
        path="/",
    )


def start_session(db, response, user_id):
    token = secrets.token_urlsafe(32)
    db.add(
        LoginSession(
            token_hash=digest(token), user_id=user_id, expires_at=time.time() + settings.session_days * 86400
        )
    )
    db.execute(delete(LoginSession).where(LoginSession.expires_at < time.time()))
    set_cookie(response, token)


def current_user(request: Request, response: Response, _: None = Depends(guard_origin)) -> User:
    token = request.cookies.get(settings.cookie_name)
    if not token:
        raise HTTPException(401, "Please sign in to continue")
    with transaction() as db:
        session = db.get(LoginSession, digest(token))
        if session is None or session.expires_at <= time.time():
            raise HTTPException(401, "Your session expired. Please sign in again.")
        user = db.get(User, session.user_id)
        if user is None:
            raise HTTPException(401, "Please sign in again")
        if session.expires_at < time.time() + (settings.session_days - 1) * 86400:
            session.expires_at = time.time() + settings.session_days * 86400
            set_cookie(response, token)
        db.expunge(user)
        return user


class Credentials(StrictModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class RecoveryCredentials(Credentials):
    recovery_code: str = Field(min_length=12, max_length=128)


def user_view(user):
    return {"id": user.id, "email": user.email}


@router.post("/register", dependencies=[Depends(guard_origin)])
def register(body: Credentials, request: Request, response: Response):
    email = str(body.email).strip().lower()
    check_attempts(request, email, "register")
    recovery_code = secrets.token_urlsafe(24)
    user = User(email=email, password_hash=hasher.hash(body.password), recovery_hash=digest(recovery_code))
    try:
        with transaction() as db:
            db.add(user)
            db.flush()
            start_session(db, response, user.id)
    except IntegrityError as exc:
        raise HTTPException(
            409, "An account with this email already exists. Sign in or use your recovery code."
        ) from exc
    return {"user": user_view(user), "recovery_code": recovery_code}


@router.post("/login", dependencies=[Depends(guard_origin)])
def login(body: Credentials, request: Request, response: Response):
    email = str(body.email).strip().lower()
    check_attempts(request, email)
    with transaction() as db:
        user = db.scalar(select(User).where(User.email == email))
        valid, upgraded = hasher.verify_and_update(body.password, user.password_hash if user else DUMMY_HASH)
        if not user or not valid:
            raise HTTPException(401, "Email or password is incorrect")
        if upgraded:
            user.password_hash = upgraded
        previous_token = request.cookies.get(settings.cookie_name)
        if previous_token:
            db.execute(delete(LoginSession).where(LoginSession.token_hash == digest(previous_token)))
        start_session(db, response, user.id)
        return {"user": user_view(user)}


@router.get("/me")
def me(user: User = Depends(current_user)):
    return {"user": user_view(user)}


@router.post("/logout", dependencies=[Depends(guard_origin)])
def logout(request: Request, response: Response):
    token = request.cookies.get(settings.cookie_name)
    if token:
        with transaction() as db:
            db.execute(delete(LoginSession).where(LoginSession.token_hash == digest(token)))
    response.delete_cookie(
        settings.cookie_name, path="/", secure=settings.production, httponly=True, samesite="lax"
    )
    return {"ok": True}


@router.post("/recover", dependencies=[Depends(guard_origin)])
def recover(body: RecoveryCredentials, request: Request):
    email = str(body.email).strip().lower()
    check_attempts(request, email, "recover")
    new_recovery = secrets.token_urlsafe(24)
    with transaction() as db:
        user = db.scalar(select(User).where(User.email == email).with_for_update())
        if not user or not secrets.compare_digest(user.recovery_hash, digest(body.recovery_code)):
            raise HTTPException(401, "Email or recovery code is incorrect")
        user.password_hash = hasher.hash(body.password)
        user.recovery_hash = digest(new_recovery)
        db.execute(delete(LoginSession).where(LoginSession.user_id == user.id))
    return {
        "recovery_code": new_recovery,
        "message": "Password updated. Save your new recovery code and sign in.",
    }
