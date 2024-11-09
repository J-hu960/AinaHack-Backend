from typing import Optional, Dict, List
from pydantic import Field, HttpUrl
from .base import TimestampedModel
from datetime import datetime

class ContenidoFormativo(TimestampedModel):
    """
    Modelo de datos para la tabla contenido_formativo
    """
    id: str
    titulo: str  # Título real de la actividad formativa
    descripcion: Optional[str] = None
    tipo: str = Field(..., pattern="^(curso|taller|master|certificacion)$")
    proveedor: Optional[str] = None
    centro_nombre: Optional[str] = None  # Nombre del centro que lo imparte
    duracion_horas: Optional[int] = None
    modalidad: str = Field(None, pattern="^(presencial|online|hibrido)$")
    nivel: str = Field(None, pattern="^(basico|intermedio|avanzado)$")
    rating: Optional[float] = Field(None, ge=0, le=5)
    metadatos: Optional[Dict] = None
    ubicacion_id: Optional[int] = None
    categorias: List[str] = Field(default_factory=list)
    fecha_publicacion: Optional[datetime] = None
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None
    plazas: Optional[int] = Field(None, ge=0)
    precio: Optional[float] = Field(None, ge=0)
    url_mas_info: Optional[HttpUrl] = None
    destacado: bool = False
    estado: str = Field("activo", pattern="^(activo|inactivo|borrador)$")