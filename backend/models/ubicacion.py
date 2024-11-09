from typing import Optional
from pydantic import Field
from .base import TimestampedModel

class Ubicacion(TimestampedModel):
    """
    Modelo de datos para la tabla ubicaciones
    """
    id: Optional[int] = None
    direccion: Optional[str] = None
    codigo_postal: Optional[str] = None
    distrito: Optional[str] = None
    barrio: Optional[str] = None
    latitud: Optional[float] = Field(None, ge=-90, le=90)
    longitud: Optional[float] = Field(None, ge=-180, le=180)