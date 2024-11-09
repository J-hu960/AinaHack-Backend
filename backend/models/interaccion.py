from typing import Optional, Dict
from pydantic import Field
from .base import TimestampedModel
from datetime import datetime

class Interaccion(TimestampedModel):
    """
    Modelo de datos para la tabla interacciones
    """
    id: Optional[int] = None
    usuario_id: int
    contenido_id: str
    tipo: str = Field(..., pattern="^(view|like|complete|save)$")
    tiempo_consumido: Optional[float] = Field(None, ge=0)
    progreso: Optional[float] = Field(None, ge=0, le=100)
    valoracion: Optional[int] = Field(None, ge=1, le=5)
    fecha: datetime = Field(default_factory=datetime.now)
    metadatos: Optional[Dict] = None