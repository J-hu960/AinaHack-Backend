

import os
from fastapi import HTTPException, APIRouter
from openai import OpenAI
from langsmith.wrappers import wrap_openai
from langsmith import traceable
from pydantic import BaseModel
from dotenv import load_dotenv
import sqlite3
from typing import List, Dict
import logging
logger = logging.getLogger(__name__)


load_dotenv()

router = APIRouter()

# Load the Hugging Face API token and base URL from the environment
HF_TOKEN = os.getenv("HF_TOKEN")
BASE_URL = os.getenv("BASE_URL")

if not HF_TOKEN or not BASE_URL:
    raise ValueError("HF_TOKEN and BASE_URL must be set in the .env file")

client = wrap_openai(OpenAI(
    base_url=f"{BASE_URL}/v1/",
    api_key=HF_TOKEN
))

class QueryRequest(BaseModel):
    request: str

class QueryResponse(BaseModel):
    answer: str
    categories: List[str] = []



@router.post("/query", tags=["RAG"])
async def query_rag(request: QueryRequest):
    try:
        pregunta = request.request
        categories = ["Educació fisica, Empleabilitat, Administració Publica, Cultura"] # Query a la BBDD
        categories_str = ", ".join(categories)
        categories_text = ask(f"Contesta les respostes separades per *,*. Busca de les categories {categories_str} de les activitats les cuals es relacionen a la seguent pregunta.", pregunta)

        cat = [c.strip() for c in categories_text.split(",")]

        activities = sql_query(cat)
        logger.info(activities)
        activities_str = ""
        if not activities:
            activities_str = "No hi han activitats, no t'inventis les activitats, no hi ha cap." 
        else:
            activities_str = "; ".join([f"{activity['nom']} - {activity['ubicacio']} ({activity['data']} {activity['hora']})" for activity in activities])
        
        answer = ask(f"Ets un expert en activitats. Aqui tens les activitats: {activities_str}. Contesta la pregunta de l'usuari.", pregunta)

        return [{"answer": answer, "activitats": activities}]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@traceable
def ask(prompt: str, question: str) -> str:
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": question}
        ]

        chat_completion = client.chat.completions.create(
            model="tgi",
            messages=messages,
            max_tokens=1000
        )

        return chat_completion.choices[0].message.content


def sql_query(categories: List[str]) -> List[Dict[str, str]]:
    conn = sqlite3.connect('activitats.db')
    cursor = conn.cursor()

    query = """
    SELECT nom, ubicacio, data, hora
    FROM activitats
    WHERE {}
    """.format(
        " OR ".join(["categories LIKE ?" for _ in categories])
    )

    params = [f'%,{category},%' for category in categories]

    cursor.execute(query, params)
    rows = cursor.fetchall()

    conn.close()

    activitats = []
    for row in rows:
        activitats.append({
            "nom": row[0],
            "ubicacio": row[1],
            "data": row[2],
            "hora": row[3]
        })

    return activitats
