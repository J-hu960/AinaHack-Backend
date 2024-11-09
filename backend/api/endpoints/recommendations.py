from typing import Dict, List, Optional
import logging
import sqlite3
import pandas as pd
import json
import os
from pathlib import Path
from crewai import Agent, Task, Crew, Process
from crewai.tools import tool  # Use the @tool decorator from CrewAI
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MemoryConfig:
    """System memory configuration"""
    def __init__(self):
        # Get base project path
        self.project_root = Path(__file__).parent.parent.parent
        # Define standard path for the DB
        self.db_dir = self.project_root / "backend" / "db"
        self.db_path = str(self.db_dir / "jaa.sqlite")
        # Create directory if it doesn't exist
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
        Initializes the content recommender
        
        Args:
            db_path (Optional[str]): Path to the database. If not provided,
                                     the default configuration will be used.
        """
        try:
            self.config = MemoryConfig()
            self.db_path = db_path if db_path else self.config.db_path

            # Verify that the database file exists
            if not os.path.exists(self.db_path):
                raise FileNotFoundError(f"Database not found at: {self.db_path}")
                
            self.setup_tools()
            self.setup_agents()
            logger.info(f"ContentRecommender initialized with DB: {self.db_path}")
                
        except Exception as e:
            logger.error(f"Error initializing ContentRecommender: {str(e)}")
            raise

    def setup_tools(self):
        """Configures the recommender's tools"""
        from crewai.tools import tool

        # Set the db_path as a constant within the tools
        DB_PATH = self.db_path

        @tool("Database Schema Analyzer")
        def analyze_schema() -> str:
            """Analyzes and extracts the complete schema of the educational database."""
            try:
                conn = sqlite3.connect(DB_PATH)
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
                logger.error(f"Error analyzing schema: {str(e)}")
                return json.dumps({"error": str(e)})

        @tool("Database Query Tool")
        def query_database(query: str) -> str:
            """Executes SQL queries on the database and returns results in JSON format.

            Parameters:
            - query: The SQL query to execute.
            """
            try:
                conn = sqlite3.connect(DB_PATH)
                df = pd.read_sql_query(query, conn)
                conn.close()
                return df.to_json(orient='records', date_format='iso', default_handler=str)
            except Exception as e:
                logger.error(f"Error in query: {str(e)}")
                return json.dumps({"error": str(e)})

        self.schema_tool = analyze_schema
        self.query_tool = query_database

    def setup_agents(self):
        """Configures the system's agents"""
        self.schema_analyzer = Agent(
            role="Database Schema Analyst",
            goal="Analyze and document the structure of the SQLite educational database",
            backstory="""Expert in educational database analysis with extensive experience in SQLite and recommendation systems.""",
            tools=[self.schema_tool],
            verbose=True,
            allow_delegation=False
        )

        self.content_analyzer = Agent(
            role="Educational Content Analyst",
            goal="Analyze content and generate personalized recommendations",
            backstory="""Specialist in educational content analysis and recommendation systems focusing on personalization.""",
            tools=[self.query_tool],
            verbose=True,
            allow_delegation=False
        )

    def generate(self, usuario_id: int) -> Dict:
        """
        Generates personalized recommendations for a user.
        
        Args:
            usuario_id (int): User ID

        Returns:
            Dict: Dictionary with recommendations
        """
        try:
            # Obtain user data and profile
            conn = sqlite3.connect(self.db_path)
            
            query = f"""
                SELECT p.tipo, p.areas_interes, p.nivel_formacion
                FROM perfiles p
                WHERE p.usuario_id = {usuario_id}
            """
            
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            if df.empty:
                raise ValueError(f"No profile found for user {usuario_id}")
            
            perfil = df.iloc[0]
            
            # Create recommendation task
            recommend_task = Task(
                description=(
                    f"As an expert recommender, analyze the following profile:\n"
                    f"- Type: {perfil['tipo']}\n"
                    f"- Interests: {perfil['areas_interes']}\n"
                    f"- Level: {perfil['nivel_formacion']}\n\n"
                    f"Use the flexible search tool to:\n"
                    f"1. Search for content related to each area of interest\n"
                    f"2. Consider synonyms and related terms\n"
                    f"3. Adapt searches to the user's level\n"
                    f"4. Prioritize content with higher ratings\n\n"
                    f"Generate the top 10 personalized recommendations in JSON format as a list."
                ),
                expected_output="""[
                    {
                        "id": "1",
                        "titulo": "Advanced Cloud Computing Course",
                        "descripcion": "Learn cloud computing...",
                        "tipo": "course", 
                        "modalidad": "online",
                        "nivel": "advanced",
                        "rating": 4.8,
                        "precio": 299.99,
                        "estado": "activo",
                        "relevancia": 0.95,
                        "match_razones": [
                            "High rating: 4.8",
                            "Direct match with interests",
                            "Appropriate educational level"
                        ]
                    }
                ]""",
                agent=self.content_analyzer
            )

            # Create and execute crew
            crew = Crew(
                agents=[self.content_analyzer],
                tasks=[recommend_task],
                process=Process.sequential,
                memory=True,
                verbose=True,
                embedder={
                    "provider": "openai",
                    "config": {
                        "model": 'text-embedding-ada-002'
                    }
                }
            )

            # Get and process results
            results = crew.kickoff()
            return json.loads(results)

        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            return {"error": str(e)}

    def reset_memories(self):
        """Resets all system memories"""
        try:
            # Use the CrewAI CLI command to reset memories
            os.system("crewai reset-memories --all")
            logger.info("Memories successfully reset")
        except Exception as e:
            logger.error(f"Error resetting memories: {str(e)}")

# Example usage
if __name__ == "__main__":
    recommender = ContentRecommender()
    recommendations = recommender.generate(usuario_id=1)
    print(json.dumps(recommendations, indent=2, ensure_ascii=False))
