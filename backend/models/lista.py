from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Boolean, ForeignKey
from .base import TimestampedModel

class Lista(TimestampedModel):
    """Modelo de datos para la tabla listas"""
    __tablename__ = 'listas'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    nombre: Mapped[str] = mapped_column(String, nullable=False)
    descripcion: Mapped[str | None] = mapped_column(String, nullable=True)
    publica: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relación con Usuario usando string
    usuario = relationship("Usuario", back_populates="listas")

    def __repr__(self):
        return f"<Lista(id={self.id}, nombre='{self.nombre}')>"