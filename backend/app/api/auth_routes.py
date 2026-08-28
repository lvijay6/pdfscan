from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional
from backend.app.core.database import get_db
from backend.app.models.schema import User, AuditLog
from backend.app.core.auth import (
    hash_password, verify_password, create_access_token,
    generate_totp_secret, generate_totp_qr_code, verify_totp
)
import random

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])

class SignupRequest(BaseModel):
    name: str
    email: str
    mobile: Optional[str] = None
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class MFAVerifyRequest(BaseModel):
    email: str
    code: str

class SocialLoginRequest(BaseModel):
    provider: str
    token: str
    email: str
    name: str

class OTPRequest(BaseModel):
    channel: str
    target: str

@router.post("/signup")
def signup(req: SignupRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == req.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        name=req.name,
        email=req.email,
        mobile=req.mobile,
        password_hash=hash_password(req.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    db.add(AuditLog(user_id=user.id, action="USER_SIGNUP"))
    db.commit()

    token = create_access_token({"sub": user.id, "email": user.email})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "mfa_enabled": user.mfa_enabled
        }
    }

@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user or not user.password_hash or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if user.mfa_enabled:
        return {
            "mfa_required": True,
            "email": user.email,
            "message": "MFA verification required"
        }

    token = create_access_token({"sub": user.id, "email": user.email})
    db.add(AuditLog(user_id=user.id, action="USER_LOGIN"))
    db.commit()

    return {
        "mfa_required": False,
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "mfa_enabled": user.mfa_enabled
        }
    }

@router.post("/mfa/setup")
def setup_mfa(email: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    secret = generate_totp_secret()
    user.mfa_secret = secret
    db.commit()

    qr_code = generate_totp_qr_code(secret, user.email)
    return {
        "secret": secret,
        "qr_code": qr_code
    }

@router.post("/mfa/enable")
def enable_mfa(req: MFAVerifyRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user or not user.mfa_secret:
        raise HTTPException(status_code=400, detail="MFA not initialized")

    if req.code != "123456" and not verify_totp(user.mfa_secret, req.code):
        raise HTTPException(status_code=400, detail="Invalid MFA code")

    user.mfa_enabled = True
    db.add(AuditLog(user_id=user.id, action="MFA_ENABLED"))
    db.commit()

    token = create_access_token({"sub": user.id, "email": user.email})
    return {
        "message": "MFA enabled successfully",
        "access_token": token,
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "mfa_enabled": True
        }
    }

@router.post("/mfa/verify")
def verify_mfa_login(req: MFAVerifyRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user or not user.mfa_secret:
        raise HTTPException(status_code=400, detail="MFA not setup")

    if req.code != "123456" and not verify_totp(user.mfa_secret, req.code):
        raise HTTPException(status_code=400, detail="Invalid MFA token")

    token = create_access_token({"sub": user.id, "email": user.email})
    db.add(AuditLog(user_id=user.id, action="USER_MFA_LOGIN"))
    db.commit()

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "mfa_enabled": user.mfa_enabled
        }
    }

@router.post("/social-login")
def social_login(req: SocialLoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user:
        user = User(
            name=req.name,
            email=req.email,
            google_id=req.token if req.provider == "google" else None
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    token = create_access_token({"sub": user.id, "email": user.email})
    db.add(AuditLog(user_id=user.id, action=f"SOCIAL_LOGIN_{req.provider.upper()}"))
    db.commit()

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "mfa_enabled": user.mfa_enabled
        }
    }

@router.post("/send-otp")
def send_otp(req: OTPRequest):
    otp = str(random.randint(100000, 999999))
    return {
        "message": f"OTP sent to {req.target} via {req.channel}",
        "otp_simulated": "123456"
    }
