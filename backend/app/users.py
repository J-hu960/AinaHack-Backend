# users.py
from fastapi import APIRouter, HTTPException, Depends, Response, status
from pydantic import BaseModel
from typing import Dict
from app.auth import get_password_hash, verify_password, create_access_token
from datetime import timedelta

router = APIRouter()

# Simulated in-memory user "database"
fake_user_db: Dict[str, Dict] = {}

class UserRegister(BaseModel):
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str


@router.post("/register")
async def register(user: UserRegister):
    if user.email in fake_user_db:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = get_password_hash(user.password)
    fake_user_db[user.email] = {"email": user.email, "password": hashed_password}
    return {"message": "User registered successfully"}

@router.post("/login")
async def login(user: UserLogin, response: Response):
    # Demo: Siempre usar usuario_id = 1
    access_token = create_access_token(
        data={
            "sub": "1",  # ID fijo para demo
            "email": user.email
        }, 
        expires_delta=timedelta(minutes=30)
    )
    
    response.set_cookie(
        key="access_token", 
        value=access_token, 
        httponly=True,
        max_age=1800,  # 30 minutos
        samesite="lax"
    )
    
    return {
        "message": "Login successful",
        "user_id": 1
    }


# @router.post("/login")
# async def login(user: UserLogin, response: Response):
#     db_user = fake_user_db.get(user.email)
#     if not db_user or not verify_password(user.password, db_user["password"]):
#         raise HTTPException(status_code=401, detail="Invalid email or password")
    
#     # Create JWT token and set it in a cookie
#     access_token = create_access_token(data={"sub": user.email}, expires_delta=timedelta(minutes=30))
#     response.set_cookie(key="access_token", value=access_token, httponly=True)
#     return {"message": "Login successful"}
