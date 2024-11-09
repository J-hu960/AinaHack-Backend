# main.py
import logging
import os
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from app.auth import create_access_token, decode_access_token
from fastapi.responses import JSONResponse
from typing import Dict

from app.chatbot import router as chatbot_router
from app.users import router as users_router
from app.recommender import ContentRecommender

app = FastAPI(
    title="AinaHack API",
    description="API para el sistema de recomendaciones de contenidos",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar los orígenes permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
async def root():
    return {"message": "Bienvenido a la API de JAA"}

@app.get("/recommendations", response_model=Dict, tags=["recommendations"])
async def get_recommendations(current_user: str = Depends(get_current_user)):
    """
    Obtiene recomendaciones personalizadas para el usuario (demo: siempre usuario 1)
    """
    try:
        user_id = 1  # ID fijo para demo
        logger.info(f"Solicitando recomendaciones para usuario {user_id}")
        recommender = ContentRecommender(db_path="db/jaa.sqlite")
        recommendations = recommender.generate(user_id)
        
        if recommendations.get("status") == "error":
            raise HTTPException(
                status_code=404, 
                detail=recommendations.get("error", "Error generando recomendaciones")
            )
            
        return recommendations
        
    except Exception as e:
        logger.error(f"Error en endpoint de recomendaciones: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error interno del servidor: {str(e)}"
        )

app.include_router(users_router, prefix="/users", tags=["users"])
app.include_router(chatbot_router, prefix="/cb", tags=["chatbot"])

