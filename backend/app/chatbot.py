

import os
from fastapi import HTTPException, APIRouter
from openai import OpenAI
from pydantic import BaseModel
from dotenv import load_dotenv


load_dotenv()

router = APIRouter()

# Load the Hugging Face API token and base URL from the environment
HF_TOKEN = os.getenv("HF_TOKEN")
BASE_URL = os.getenv("BASE_URL")

if not HF_TOKEN or not BASE_URL:
    raise ValueError("HF_TOKEN and BASE_URL must be set in the .env file")

client = OpenAI(
    base_url=f"{BASE_URL}/v1/",
    api_key=HF_TOKEN
)

class QueryRequest(BaseModel):
    question: str

@router.post("/query", tags=["RAG"])
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
