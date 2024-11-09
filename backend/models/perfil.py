from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, DateTime, JSON, ForeignKey
from .base import TimestampedModel
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .usuario import Usuario

class Perfil(TimestampedModel):
    """Modelo de datos para la tabla perfiles"""
    __tablename__ = 'perfiles'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    tipo: Mapped[str] = mapped_column(String, nullable=False)
    areas_interes: Mapped[list] = mapped_column(JSON, default=list)
    nivel_formacion: Mapped[str | None] = mapped_column(String, nullable=True)
    situacion_laboral: Mapped[str | None] = mapped_column(String, nullable=True)
    objetivos: Mapped[list] = mapped_column(JSON, default=list)
    ultima_actualizacion: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relación con Usuario
    usuario: Mapped["Usuario"] = relationship(back_populates="perfil")