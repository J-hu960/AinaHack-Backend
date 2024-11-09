from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, DateTime, JSON
from .base import TimestampedModel
from datetime import datetime
from typing import List, Optional

class Usuario(TimestampedModel):
    """Modelo de datos para la tabla usuarios"""
    __tablename__ = 'usuarios'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)
    fecha_registro: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    status: Mapped[str] = mapped_column(String, default='activo')
    preferencias: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Relaciones usando strings para evitar referencias circulares
    perfil = relationship("Perfil", back_populates="usuario", uselist=False)
    listas = relationship("Lista", back_populates="usuario", lazy="dynamic")

    def __repr__(self):
        return f"<Usuario(id={self.id}, email='{self.email}')>"