from typing import Optional
from pydantic import Field
from .base import TimestampedModel

class Categoria(TimestampedModel):
    """
    Modelo de datos para la tabla categorias
    """
    id: Optional[int] = None
    nombre: str
    descripcion: Optional[str] = None
    tipo: str = Field(..., pattern="^(area|nivel|modalidad)$")
    activa: bool = True