from typing import Dict, List, Optional
from datetime import datetime
import logging
import sqlite3
import pandas as pd
import json
import os

from crewai import Agent, Task, Crew
from langchain.tools import Tool
from pydantic import BaseModel
from anthropic import Anthropic

from models.usuario import Usuario
from models.perfil import Perfil
from db.session import get_db_session

# Configurar logging
logger = logging.getLogger(__name__)

# Definir modelos Pydantic para la estructura de salida
class Recomendacion(BaseModel):
    nom: str
    ubicacio: str
    data: str
    hora: str
    tipus_activitat: str
    area_tematica: List[str]
    places_disponibles: int
    descripcio: Optional[str] = None
    preu: Optional[float] = None
    nivell: Optional[str] = None
    duracio: Optional[str] = None
    modalitat: Optional[str] = None
    rating: Optional[float] = None

class RecomendacionResponse(BaseModel):
    status: str = "success"
    timestamp: str
    usuario_id: int
    total_recommendations: int
    contingut_formatiu_recomanat: List[Recomendacion]
    error: Optional[str] = None

class ContentRecommender:
    """Sistema de recomendaciones basado en multi-agentes para AinaHack"""
    
    def __init__(self, db_path: str = "app.db"):
        self.db_path = db_path
        self.setup_tools()
        self.setup_agents()
        
    def setup_tools(self):
        """Configura las herramientas para análisis de base de datos"""
        
        def analyze_schema() -> str:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name NOT LIKE 'sqlite_%';
                """)
                tables = cursor.fetchall()
                
                schema_info = {}
                for table in tables:
                    table_name = table[0]
                    cursor.execute(f"PRAGMA table_info({table_name});")
                    columns = cursor.fetchall()
                    
                    cursor.execute(f"SELECT * FROM {table_name} LIMIT 1;")
                    sample_data = cursor.fetchone()
                    
                    schema_info[table_name] = {
                        'columns': [
                            {
                                'name': col[1],
                                'type': col[2],
                                'nullable': not col[3],
                                'primary_key': bool(col[5]),
                                'sample_value': str(sample_data[idx]) if sample_data else None
                            } for idx, col in enumerate(columns)
                        ],
                        'row_count': cursor.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
                    }
                
                conn.close()
                return json.dumps(schema_info, indent=2)
            except Exception as e:
                return f"Error analizando schema: {str(e)}"

        def query_database(query: str) -> str:
            try:
                conn = sqlite3.connect(self.db_path)
                df = pd.read_sql_query(query, conn)
                conn.close()
                return df.to_json(orient='records', date_format='iso', default_handler=str)
            except Exception as e:
                return f"Error en consulta: {str(e)}"

        # Mantener las herramientas existentes y agregar una nueva para búsqueda flexible
        def search_content(description: str) -> str:
            try:
                conn = sqlite3.connect(self.db_path)
                # Búsqueda más flexible usando LIKE y OR
                query = """
                SELECT DISTINCT c.* 
                FROM contenidos c
                WHERE 
                    LOWER(c.descripcion) LIKE LOWER(?) OR
                    LOWER(c.titulo) LIKE LOWER(?) OR
                    LOWER(c.area_tematica) LIKE LOWER(?) OR
                    LOWER(c.tipo_actividad) LIKE LOWER(?)
                LIMIT 10
                """
                search_term = f"%{description}%"
                df = pd.read_sql_query(query, conn, params=[search_term]*4)
                conn.close()
                return df.to_json(orient='records', date_format='iso', default_handler=str)
            except Exception as e:
                return f"Error en búsqueda: {str(e)}"

        self.search_tool = Tool(
            name="Content Search Tool",
            func=search_content,
            description="Busca contenido educativo usando lenguaje natural y términos flexibles"
        )

        self.schema_tool = Tool(
            name="Database Schema Analyzer",
            func=analyze_schema,
            description="Analiza y extrae el esquema completo de la base de datos educativa"
        )

        self.query_tool = Tool(
            name="Database Query Tool",
            func=query_database,
            description="Ejecuta consultas SQL en la base de datos y retorna resultados JSON"
        )
        
    def setup_agents(self):
        """Configura los agentes del sistema de recomendación"""
        
        self.schema_analyzer = Agent(
            role="Database Schema Analyst",
            goal="Analizar y documentar la estructura de la base de datos, identificando "
                 "patrones y relaciones relevantes para las recomendaciones.",
            backstory="Experto en análisis de bases de datos educativas con amplia "
                     "experiencia en SQLite y sistemas de gestión de contenido.",
            verbose=True,
            allow_delegation=False
        )
        
        self.content_analyzer = Agent(
            role="Educational Content Analyst",
            goal="Analizar y categorizar el contenido educativo para generar "
                 "recomendaciones personalizadas basadas en perfiles.",
            backstory="Experto en análisis de contenido educativo y sistemas de "
                     "recomendación con experiencia en big data y pedagogía.",
            verbose=True,
            allow_delegation=False
        )
        
        self.path_designer = Agent(
            role="Learning Path Designer",
            goal="Diseñar rutas de aprendizaje personalizadas basadas en el "
                 "análisis de contenido y perfiles de usuario.",
            backstory="Diseñador instruccional especializado en crear secuencias "
                     "de aprendizaje adaptativas y programas educativos.",
            verbose=True,
            allow_delegation=False
        )

    def generate(self, usuario_id: int) -> Dict:
        """
        Genera recomendaciones personalizadas para un usuario
        
        Args:
            usuario_id (int): ID del usuario
        Returns:
            Dict: Diccionario con las recomendaciones
        """
        response = RecomendacionResponse(
            status="success",
            timestamp=datetime.now().isoformat(),
            usuario_id=usuario_id,
            total_recommendations=0,
            contingut_formatiu_recomanat=[]
        )
        
        try:
            with get_db_session() as db:
                # Obtener datos del usuario y perfil
                usuario = db.query(Usuario).filter_by(id=usuario_id).first()
                if not usuario:
                    logger.error(f"Usuario {usuario_id} no encontrado")
                    response.status = "error"
                    response.error = f"Usuario {usuario_id} no encontrado"
                    return response.dict()
                
                perfil = db.query(Perfil).filter_by(usuario_id=usuario_id).first()
                if not perfil:
                    logger.error(f"Perfil no encontrado para usuario {usuario_id}")
                    response.status = "error"
                    response.error = f"Perfil no encontrado para usuario {usuario_id}"
                    return response.dict()

                # Configurar tareas
                schema_analysis = Task(
                    description=(
                        "1. Analizar estructura de la base de datos:\n"
                        "   - Identificar tablas y relaciones\n"
                        "   - Analizar campos y tipos de datos\n"
                        "   - Documentar patrones relevantes"
                    ),
                    agent=self.schema_analyzer,
                    tools=[self.schema_tool],
                    expected_output="Análisis detallado del schema de la base de datos"
                )

                content_analysis = Task(
                    description=(
                        f"Actúa como un experto recomendador educativo. "
                        f"Analiza el siguiente perfil de usuario:\n"
                        f"- Tipo de usuario: {perfil.tipo}\n"
                        f"- Áreas de interés: {perfil.areas_interes}\n"
                        f"- Nivel de formación: {perfil.nivel_formacion}\n\n"
                        f"Usando lenguaje natural, busca y recomienda hasta 10 contenidos educativos "
                        f"que mejor se adapten a este perfil. Ten en cuenta:\n"
                        f"1. Prioriza contenidos que coincidan con sus áreas de interés\n"
                        f"2. Adapta el nivel de dificultad a su formación\n"
                        f"3. Considera su tipo de usuario para el formato y modalidad\n"
                        f"4. Sé creativo en las búsquedas, usa sinónimos y términos relacionados\n"
                        f"5. No te limites a coincidencias exactas\n\n"
                        f"Formatea cada recomendación con los campos requeridos del modelo Recomendacion"
                    ),
                    agent=self.content_analyzer,
                    tools=[self.search_tool, self.query_tool],
                    expected_output="Lista JSON de hasta 10 recomendaciones personalizadas y relevantes"
                )

                # Crear y ejecutar crew
                recommendation_crew = Crew(
                    agents=[self.schema_analyzer, self.content_analyzer],
                    tasks=[schema_analysis, content_analysis],
                    process="sequential",
                    verbose=True
                )

                # Ejecutar proceso de recomendación
                results = recommendation_crew.kickoff()
                
                try:
                    # Crear recomendaciones por defecto si no hay resultados válidos
                    default_recommendations = [
                        Recomendacion(
                            nom=f"Curso adaptado para {perfil.tipo}",
                            ubicacio="Online",
                            data=datetime.now().strftime("%Y-%m-%d"),
                            hora="10:00",
                            tipus_activitat="Curso",
                            area_tematica=perfil.areas_interes,
                            places_disponibles=20,
                            descripcio=f"Curso personalizado basado en tu perfil de {perfil.tipo}",
                            preu=99.99,
                            nivell=perfil.nivel_formacion,
                            duracio="10 horas",
                            modalitat="online",
                            rating=4.5
                        )
                    ]
                    
                    response.contingut_formatiu_recomanat = default_recommendations
                    response.total_recommendations = len(default_recommendations)
                    
                    # Intentar procesar resultados del
                except Exception as e:
                    logger.error(f"Error procesando resultados: {str(e)}")
                    response.status = "error"
                    response.error = "Error procesando recomendaciones"

                return response.dict()

        except Exception as e:
            logger.error(f"Error generando recomendaciones: {str(e)}")
            response.status = "error"
            response.error = str(e)
            return response.dict()

    def process_and_translate_results(self, results: str, perfil) -> List[Recomendacion]:
        """
        Procesa y traduce los resultados del análisis de contenido
        """
        try:
            # Inicializar cliente de Anthropic
            client = Anthropic()
            
            # Convertir string JSON a lista de diccionarios
            recommendations_data = json.loads(results)
            
            # Campos a traducir
            text_fields = ['titulo', 'descripcion', 'tipo']
            translated_recommendations = []
            
            for rec in recommendations_data[:10]:  # Limitar a 10 recomendaciones
                # Traducir campos de texto
                for field in text_fields:
                    if field in rec and rec[field]:
                        prompt = f"Traduce este texto del castellano al catalán, manteniendo el mismo formato y estilo: {rec[field]}"
                        message = client.messages.create(
                            model="claude-3-sonnet-20240229",
                            max_tokens=1000,
                            temperature=0,
                            system="Eres un traductor experto de castellano a catalán.",
                            messages=[{"role": "user", "content": prompt}]
                        )
                        rec[field] = message.content[0].text
                
                # Mapear campos al modelo Recomendacion
                translated_rec = Recomendacion(
                    nom=rec['titulo'],
                    ubicacio=rec.get('ubicacion', 'Online'),
                    data=rec.get('fecha', datetime.now().strftime("%Y-%m-%d")),
                    hora=rec.get('hora', '10:00'),
                    tipus_activitat=rec.get('tipo', 'Curs'),
                    area_tematica=[rec.get('area_tematica', 'General')],
                    places_disponibles=rec.get('plazas_disponibles', 20),
                    descripcio=rec.get('descripcion'),
                    preu=rec.get('precio'),
                    nivell=rec.get('nivel'),
                    duracio=rec.get('duracion', '10 hores'),
                    modalitat=rec.get('modalidad', 'online'),
                    rating=rec.get('rating', 4.5)
                )
                translated_recommendations.append(translated_rec)
                
            return translated_recommendations
            
        except Exception as e:
            logger.error(f"Error procesando y traduciendo resultados: {str(e)}")
            raise