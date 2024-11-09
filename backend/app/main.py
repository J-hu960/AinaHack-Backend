# main.py
import logging
import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

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

# Load the Hugging Face API token and base URL from the environment
HF_TOKEN = os.getenv("HF_TOKEN")
BASE_URL = os.getenv("BASE_URL")

if not HF_TOKEN or not BASE_URL:
    raise ValueError("HF_TOKEN and BASE_URL must be set in the .env file")

# Initialize the OpenAI client with the Hugging Face Inference API
client = OpenAI(
    base_url=f"{BASE_URL}/v1/",
    api_key=HF_TOKEN
)

class QueryRequest(BaseModel):
    question: str

@app.get("/", tags=["root"])
async def root():
    return {"message": "Hello World"}

@app.post("/query", tags=["RAG"])
async def query_rag(request: QueryRequest):
    try:
        # Prepare the messages for the chat completion
        messages = [
            {"role": "system", "content": "Ets un asistent recomanador que s'encarrega de recomanar activitats."},
            {"role": "user", "content": request.question}
        ]

        # Call the chat completion endpoint
        chat_completion = client.chat.completions.create(
            model="tgi",
            messages=messages,
            max_tokens=1000
        )

        # Extract the response text
        answer = chat_completion.choices[0].message.content
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
