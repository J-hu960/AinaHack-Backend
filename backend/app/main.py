# main.py
import logging
import os
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from app.auth import create_access_token, decode_access_token
from fastapi.responses import JSONResponse

from app.chatbot import router as chatbot_router
from app.users import router as users_router
import app.recommender




app = FastAPI()

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://miav030-525373923741.europe-southwest1.run.app",
        "https://v030-backend-525373923741.europe-southwest1.run.app",
        "https://miav030-dev-525373923741.europe-southwest1.run.app",
        "https://v030-dev-backend-525373923741.europe-southwest1.run.app",
        "http://localhost:5173",
        "http://localhost:8080",
        "ws://localhost:8080",
        "wss://localhost:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response

@app.exception_handler(Exception)
async def custom_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})

@app.get("/error")
async def create_error():
    raise ValueError("This is a test error to trigger logging.")

async def get_current_user(request: Request):
    token = request.cookies.get("access_token")
    if token is None:
        raise HTTPException(status_code=403, detail="Not authenticated")
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=403, detail="Invalid session")
    return payload["sub"]

@app.get("/", tags=["root"])
async def root(user: str = Depends(get_current_user)):
    return {
        "recommendation": recommender.generate(),
        "trending": recommender.trending(),
    }

app.include_router(users_router, prefix="/users", tags=["users"])
app.include_router(chatbot_router, prefix="/cb", tags=["chatbot"])

