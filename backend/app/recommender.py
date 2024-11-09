from typing import Dict, List, Optional
import logging
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        orm_mode = True

class ContentRecommender:
    def __init__(self, db_path: Optional[str] = None):
        """
        Initializes the content recommender
        """
        logger.info("Inicializando ContentRecommender con datos fake")

    def generate(self, usuario_id: int) -> List[Dict]:
        """
        Generates fake personalized recommendations for testing.
        
        Args:
            usuario_id: User ID to generate recommendations for
            
        Returns:
            List[Dict]: List of fake recommendations
        """
        try:
            fake_recommendations = [
                {
                    "id": "1001",
                    "titulo": "Curso online de Tecnologías Hispánicas: Explorando el Mundo Digital en Español",
                    "descripcion": "Sumérgete en el fascinante universo de las tecnologías hispánicas con este curso online de nivel intermedio. A lo largo de 46 horas de formación, adquirirás conocimientos y habilidades clave para destacar en el ámbito tecnológico desde una perspectiva hispana.",
                    "tipo": "curso",
                    "modalidad": "online",
                    "nivel": "intermedio",
                    "rating": 4.6,
                    "precio": 299.0,
                    "estado": "activo",
                    "relevancia": 0.95,
                    "match_razones": [
                        "Alto rating: 4.6",
                        "Modalidad online preferida",
                        "Nivel adecuado al perfil"
                    ]
                },
                {
                    "id": "1002",
                    "titulo": "Curso online de Tecniber-5: Formación especializada en tecnología e informática",
                    "descripcion": "Este curso online de nivel intermedio en Tecniber-5 te brinda una formación especializada en el ámbito de la tecnología e informática. A lo largo de 46 horas, adquirirás conocimientos y habilidades clave para destacar en este campo profesional en constante evolución.",
                    "tipo": "curso",
                    "modalidad": "presencial",
                    "nivel": "intermedio",
                    "rating": 4.6,
                    "precio": 299.0,
                    "estado": "activo",
                    "relevancia": 0.85,
                    "match_razones": [
                        "Alto rating: 4.6",
                        "Temática relevante",
                        "Nivel adecuado al perfil"
                    ]
                },
                {
                    "id": "1003",
                    "titulo": "Curso online de Informática en Vipe Escola d'Informàtica",
                    "descripcion": "Curso online de nivel intermedio en el campo de la informática, ofrecido por Vipe Escola d'Informàtica. Esta formación te permitirá adquirir conocimientos y habilidades avanzadas en el área de la tecnología de la información.",
                    "tipo": "curso",
                    "modalidad": "presencial",
                    "nivel": "intermedio",
                    "rating": 3.4,
                    "precio": 265.0,
                    "estado": "activo",
                    "relevancia": 0.75,
                    "match_razones": [
                        "Precio competitivo",
                        "Temática relacionada",
                        "Centro especializado"
                    ]
                }
            ]
            
            logger.info(f"Generadas {len(fake_recommendations)} recomendaciones fake para usuario {usuario_id}")
            return fake_recommendations
            
        except Exception as e:
            logger.error(f"Error generando recomendaciones fake: {str(e)}")
            return {"error": str(e)}

if __name__ == "__main__":
    recommender = ContentRecommender()
    recommendations = recommender.generate(usuario_id=1)
    print(json.dumps(recommendations, indent=2, ensure_ascii=False))
