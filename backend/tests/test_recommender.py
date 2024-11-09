import sys
import os
from pathlib import Path
import logging
import json
from dotenv import load_dotenv
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Configurar el path para incluir el directorio raíz del proyecto
current_dir = Path(__file__).parent
backend_dir = current_dir.parent
sys.path.append(str(backend_dir))

# Ahora podemos importar los módulos del proyecto
from db.session import Base, get_db_session
from app.recommender import ContentRecommender
from models.usuario import Usuario
from models.perfil import Perfil
from models.lista import Lista

# Cargar variables de entorno
load_dotenv()

# Configurar logging más detallado   
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_recommender.log')
    ]
)

# Configurar logging para SQLAlchemy y CrewAI
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
logging.getLogger('crewai').setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)

@pytest.fixture(scope="session")
def test_db():
    """Crear una base de datos de prueba temporal"""
    try:
        logger.info("Iniciando configuración de base de datos de prueba")
        db_path = backend_dir / "db" / "jaa.sqlite"
        os.makedirs(db_path.parent, exist_ok=True)
        logger.debug(f"Usando base de datos en: {db_path}")
        
        engine = create_engine(f"sqlite:///{db_path}", echo=True)
        
        logger.info("Creando tablas en la base de datos")
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(bind=engine)
        
        with get_db_session() as db:
            logger.info("Sesión de base de datos iniciada")
            yield db
            logger.info("Sesión de base de datos finalizada")
            
    except Exception as e:
        logger.error(f"Error en configuración de BD: {str(e)}")
        raise

def test_recommendations(test_db):
    """Script para probar el sistema de recomendaciones"""
    try:
        logger.info("=== Iniciando pruebas del sistema de recomendaciones ===")
        
        # Crear instancia del recomendador
        logger.debug("Creando instancia del recomendador")
        recommender = ContentRecommender(db_path=str(backend_dir / "db" / "jaa.sqlite"))
        logger.info("Recomendador inicializado correctamente")
        
        # Lista de IDs de usuario para probar
        test_user_ids = [4]
        
        for user_id in test_user_ids:
            logger.info(f"\n=== Procesando usuario {user_id} ===")
            
            try:
                logger.debug(f"Generando recomendaciones para usuario {user_id}")
                recommendations = recommender.generate(user_id)
                
                if recommendations is None:
                    raise ValueError("El recomendador devolvió None")
                
                logger.debug("Recomendaciones generadas exitosamente")
                logger.info("Recomendaciones detalladas:")
                logger.info(json.dumps(recommendations, indent=2, ensure_ascii=False))
                
            except Exception as e:
                logger.error(f"Error procesando usuario {user_id}")
                logger.error(f"Detalles del error: {str(e)}")
                logger.exception("Stacktrace completo:")
                continue
                
        logger.info("=== Pruebas completadas ===")
        
    except Exception as e:
        logger.error("Error general en las pruebas")
        logger.error(f"Detalles del error: {str(e)}")
        logger.exception("Stacktrace completo:")
        raise

if __name__ == "__main__":
    pytest.main(["-v", "--capture=no", __file__])