from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from contextlib import contextmanager
import logging
from typing import Generator
import os
from pathlib import Path

# Configurar logging
logger = logging.getLogger(__name__)

# Obtener la ruta absoluta al directorio de la base de datos
DB_DIR = Path(__file__).parent.parent
DB_PATH = os.path.join(DB_DIR, "db", "jaa.sqlite")

# Crear URL de la base de datos asegurando que la ruta es absoluta
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Crear engine con configuración mejorada
engine = create_engine(
    DATABASE_URL,
    echo=True,  # Activar para ver las consultas SQL durante el desarrollo
    pool_pre_ping=True,
    connect_args={
        "check_same_thread": False,  # Necesario para SQLite
        "timeout": 30  # Timeout en segundos
    }
)

# Crear SessionLocal con configuración optimizada
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False  # Mejora el rendimiento
)

# Base para modelos declarativos
Base = declarative_base()

@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Contexto para manejar sesiones de base de datos de forma segura
    
    Yields:
        Session: Sesión de SQLAlchemy configurada
    
    Raises:
        Exception: Cualquier error durante las operaciones de base de datos
    """
    db = SessionLocal()
    try:
        logger.debug("Iniciando nueva sesión de base de datos")
        yield db
        db.commit()
        logger.debug("Sesión comprometida exitosamente")
    except Exception as e:
        db.rollback()
        logger.error(f"Error en sesión de base de datos: {str(e)}")
        raise
    finally:
        db.close()
        logger.debug("Sesión cerrada")

def get_db() -> Generator[Session, None, None]:
    """
    Generador de sesiones para uso con FastAPI Depends
    
    Yields:
        Session: Sesión de SQLAlchemy configurada
    """
    with get_db_session() as session:
        yield session