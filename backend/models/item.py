from typing import Optional
from .base import TimestampedModel
from datetime import datetime
from pydantic import Field

class ItemLista(TimestampedModel):
    """
    Modelo de datos para la tabla items_lista
    """
    id: Optional[int] = None
    lista_id: int
    contenido_id: str
    orden: Optional[int] = None
    fecha_agregado: datetime = Field(default_factory=datetime.now)