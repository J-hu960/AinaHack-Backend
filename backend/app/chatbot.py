

import os
from fastapi import HTTPException, APIRouter, UploadFile, File
from openai import OpenAI
from langsmith.wrappers import wrap_openai
from langsmith import traceable
from pydantic import BaseModel
from dotenv import load_dotenv
import sqlite3
from typing import List, Dict
import requests
import logging
logger = logging.getLogger(__name__)


load_dotenv()

router = APIRouter()

HF_TOKEN = os.getenv("HF_TOKEN")
BASE_URL = os.getenv("BASE_URL")
WHISPER_API_URL = os.getenv("WHISPER_API_URL")

if not HF_TOKEN or not BASE_URL:
    raise ValueError("HF_TOKEN, BASE_URL and WHISPER_API_URL must be set in the .env file")

client = wrap_openai(OpenAI(
    base_url=f"{BASE_URL}/v1/",
    api_key=HF_TOKEN
))

whisper_headers = {
    "Accept": "application/json",
    "Authorization": f"Bearer {HF_TOKEN}",
    "Content-Type": "audio/wav",
}

class QueryRequest(BaseModel):
    request: str

class QueryResponse(BaseModel):
    answer: str
    categories: List[str] = []

DB_PATH = './db/jaa.sqlite'

def transcribe_audio(file: UploadFile):
    try:
        with file.file as audio_data:
            response = requests.post(WHISPER_API_URL, headers=whisper_headers, data=audio_data.read())
        response.raise_for_status()
        transcription = response.json().get("text", "")
        if not transcription:
            raise ValueError("Transcription failed or returned empty text")
        return transcription
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audio transcription error: {str(e)}")

@router.post("/audio-query", tags=["RAG"])
async def audio_query(file: UploadFile = File(...)):
    try:
        transcription = transcribe_audio(file)
        
        response = await query_rag(QueryRequest(request=transcription))
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/query", tags=["RAG"])
async def query_rag(request: QueryRequest):
    try:
        pregunta = request.request
        categories = get_categories()
        categories_str = ", ".join(categories)
        logger.info(f"\n\n{categories_str}\n\n")
        categories_text = ask(f"Contesta les respostes separades per *,*. Busca de les categories {categories_str} de les activitats les cuals es relacionen a la seguent pregunta.", pregunta)

        cat = [c.strip() for c in categories_text.split(",")]

        activities = sql_query(cat)
        logger.info(f"\n\n{activities}\n\n")
        answer = ""
        if not activities:
            answer = ask(pregunta, f"No hi han activitats, no contestis sobre les activitats.")
        else:
            activities_str = "; ".join([f"{activity['titol']} - {activity['descripcio']} ({activity['tipo']} {activity['modalidad']} {activity['nivel']} {activity['rating']} {activity['precio']} {activity['estado']} )" for activity in activities])
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

def get_categories():

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    query = "SELECT nombre FROM categorias WHERE activa = 1"
    
    cursor.execute(query)
    
    resultats = cursor.fetchall()
    
    conn.close()
    
    noms_categories = [row[0] for row in resultats]
    
    return noms_categories


def sql_query(nombres_categorias):

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    query = """
    SELECT 
        cf.titulo,
        cf.descripcion,
        cf.tipo,
        cf.modalidad,
        cf.nivel,
        cf.rating,
        cf.precio,
        cf.estado
    FROM contenido_formativo AS cf
    JOIN contenido_categorias AS cc ON cf.id = cc.contenido_id
    JOIN categorias AS c ON cc.categoria_id = c.id
    WHERE c.nombre IN ({placeholders})
    GROUP BY cf.id
    """.format(placeholders=", ".join("?" for _ in nombres_categorias))
    
    cursor.execute(query, nombres_categorias)
    
    resultados = cursor.fetchall()
    
    conn.close()
    
    contenido_formativo = [
        {
            "titulo": row[0],
            "descripcion": row[1],
            "tipo": row[2],
            "modalidad": row[3],
            "nivel": row[4],
            "rating": row[5],
            "precio": row[6],
            "estado": row[7]
        }
        for row in resultados
    ]
    
    return contenido_formativo
