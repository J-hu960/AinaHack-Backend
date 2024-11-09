from typing import Dict, List, Optional
from datetime import datetime
import logging
import sqlite3
import pandas as pd
import json
import os
from pathlib import Path
from crewai import Agent, Task, Crew, Process
from langchain.tools import Tool
from pydantic import BaseModel

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MemoryConfig:
    """Configuración del sistema de memoria"""
    def __init__(self):
        # Obtener ruta base del proyecto
        self.project_root = Path(__file__).parent.parent.parent
        # Definir ruta estándar para la BD
        self.db_dir = self.project_root / "backend" / "db"
        self.db_path = str(self.db_dir / "jaa.sqlite")
        # Crear directorio si no existe
        os.makedirs(self.db_dir, exist_ok=True)

class Recomendacion(BaseModel):
    id: str
    titulo: str
    descripcion: str
    tipo: str
    modalidad: str
    nivel: Optional[str]
    rating: Optional[float]
    precio: Optional[float]
    estado: str = "activo"
    relevancia: Optional[float] = None
    match_razones: Optional[List[str]] = None

    class Config:
        from_attributes = True

class ContentRecommender:
    def __init__(self, db_path: Optional[str] = None):
        """
        Inicializa el recomendador de contenido
        
        Args:
            db_path (Optional[str]): Ruta a la base de datos. Si no se proporciona,
                                   se usará la configuración por defecto.
        """
        self.config = MemoryConfig()
        self.db_path = db_path if db_path else self.config.db_path
        self.setup_tools()
        self.setup_agents()
    
    def analyze_schema(self) -> str:
        """Analiza y extrae el esquema de la base de datos educativa"""
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
            logger.error(f"Error analizando schema: {str(e)}")
            return json.dumps({"error": str(e)})

    def query_database(self, query: str) -> str:
        """Consulta y analiza el contenido de la base de datos educativa"""
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query(query, conn)
            conn.close()
            return df.to_json(orient='records', date_format='iso', default_handler=str)
        except Exception as e:
            logger.error(f"Error en consulta: {str(e)}")
            return json.dumps({"error": str(e)})

    def setup_tools(self):
        """Configura las herramientas del recomendador"""
        self.schema_tool = Tool(
            name="Database Schema Analyzer",
            func=self.analyze_schema,
            description="Analiza y extrae el esquema completo de la base de datos educativa"
        )

        self.query_tool = Tool(
            name="Database Query Tool",
            func=self.query_database,
            description="Ejecuta consultas SQL en la base de datos y retorna los resultados en formato JSON"
        )

    def setup_agents(self):
        """Configura los agentes del sistema"""
        self.schema_analyzer = Agent(
            role="Database Schema Analyst",
            goal="Analizar y documentar la estructura de la base de datos SQLite",
            backstory="""Experto en análisis de bases de datos educativas con amplia 
                     experiencia en SQLite y sistemas de recomendación.""",
            tools=[self.schema_tool],
            verbose=True
        )

        self.content_analyzer = Agent(
            role="Educational Content Analyst",
            goal="Analizar contenido y generar recomendaciones personalizadas",
            backstory="""Especialista en análisis de contenido educativo y sistemas 
                     de recomendación con enfoque en personalización.""",
            tools=[self.query_tool],
            verbose=True
        )

    def generate(self, usuario_id: int) -> Dict:
        """
        Genera recomendaciones personalizadas para un usuario
        
        Args:
            usuario_id (int): ID del usuario
        Returns:
            Dict: Diccionario con las recomendaciones
        """
        try:
            # Obtener datos del usuario y perfil
            conn = sqlite3.connect(self.db_path)
            
            query = f"""
                SELECT p.tipo, p.areas_interes, p.nivel_formacion
                FROM perfiles p
                WHERE p.usuario_id = {usuario_id}
            """
            
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            if df.empty:
                raise ValueError(f"No se encontró perfil para el usuario {usuario_id}")
            
            perfil = df.iloc[0]
            
            # Crear tarea de recomendación
            recommend_task = Task(
                description=(
                    f"Como experto recomendador, analiza el siguiente perfil:\n"
                    f"- Tipo: {perfil['tipo']}\n"
                    f"- Intereses: {perfil['areas_interes']}\n"
                    f"- Nivel: {perfil['nivel_formacion']}\n\n"
                    f"Usa la herramienta de búsqueda flexible para:\n"
                    f"1. Buscar contenido relacionado con cada área de interés\n"
                    f"2. Considerar sinónimos y términos relacionados\n"
                    f"3. Adaptar las búsquedas al nivel del usuario\n"
                    f"4. Priorizar contenido con mejor rating\n\n"
                    f"Genera las 10 mejores recomendaciones personalizadas."
                ),
                expected_output="""[
                    {
                        "id": 1,
                        "titulo": "Curso Avanzado de Cloud Computing",
                        "descripcion": "Aprende cloud computing...",
                        "tipo": "curso", 
                        "modalidad": "online",
                        "nivel": "avanzado",
                        "rating": 4.8,
                        "precio": 299.99,
                        "estado": "activo",
                        "relevancia": 0.95,
                        "match_razones": [
                            "Rating alto: 4.8",
                            "Coincidencia directa con intereses",
                            "Nivel educativo apropiado"
                        ]
                    }
                ]""",
                agent=self.content_analyzer
            )

            # Crear y ejecutar crew con memoria habilitada
            crew = Crew(
                agents=[self.content_analyzer],
                tasks=[recommend_task],
                process=Process.sequential,
                memory=True,  # Habilitar sistema de memoria
                verbose=True,
                embedder={
                    "provider": "openai",
                    "config": {
                        "model": 'text-embedding-3-small'
                    }
                }
            )

            # Obtener y procesar resultados
            results = crew.kickoff()
            return json.loads(results)

        except Exception as e:
            logger.error(f"Error generando recomendaciones: {str(e)}")
            return {"error": str(e)}

    def reset_memories(self):
        """Reinicia todas las memorias del sistema"""
        try:
            # Usar el comando CLI de crewai para resetear memorias
            os.system("crewai reset-memories --all")
            logger.info("Memorias reiniciadas exitosamente")
        except Exception as e:
            logger.error(f"Error reiniciando memorias: {str(e)}")

# Ejemplo de uso
if __name__ == "__main__":
    recommender = ContentRecommender()
    recommendations = recommender.generate(user_id=1)
    print(json.dumps(recommendations, indent=2, ensure_ascii=False))