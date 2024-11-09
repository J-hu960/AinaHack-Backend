from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import logging
from pydantic import BaseModel, Field
from typing import Optional, List as TypeList

from db.session import get_db_session
from app.recommender import ContentRecommender

logger = logging.getLogger(__name__)
router = APIRouter()

class Recomendacion(BaseModel):
    titulo: str
    descripcion: str
    tipo: str
    modalidad: str
    nivel: Optional[str] = None
    rating: Optional[float] = None
    precio: Optional[float] = None
    estado: str = "activo"
    relevancia: Optional[float] = Field(None, ge=0, le=1)
    match_razones: Optional[TypeList[str]] = Field(default_factory=list)

    class Config:
        from_attributes = True

@router.get("/recommendations/{user_id}", response_model=List[Recomendacion])
async def get_recommendations(
    user_id: int,
    db: Session = Depends(get_db_session)
):
    """
    Endpoint para obtener recomendaciones personalizadas para un usuario
    
    Args:
        user_id: ID del usuario
        db: Sesión de base de datos
    
    Returns:
        List[Recomendacion]: Lista de recomendaciones personalizadas
    """
    try:
        logger.info(f"Solicitando recomendaciones para usuario {user_id}")
        
        recommender = ContentRecommender()
        recommendations = recommender.generate(user_id)
        
        if isinstance(recommendations, dict) and recommendations.get("error"):
            logger.error(f"Error del recomendador: {recommendations['error']}")
            raise HTTPException(
                status_code=404, 
                detail=recommendations["error"]
            )
        
        # Validar y convertir cada recomendación al modelo
        validated_recommendations = []
        for rec in recommendations:
            try:
                validated_rec = Recomendacion(
                    titulo=rec["titulo"],
                    descripcion=rec["descripcion"],
                    tipo=rec["tipo"],
                    modalidad=rec["modalidad"],
                    nivel=rec.get("nivel"),
                    rating=rec.get("rating"),
                    precio=rec.get("precio"),
                    estado=rec.get("estado", "activo"),
                    relevancia=rec.get("relevancia"),
                    match_razones=rec.get("match_razones", [])
                )
                validated_recommendations.append(validated_rec)
            except Exception as e:
                logger.error(f"Error validando recomendación: {str(e)}", exc_info=True)
                continue
                
        if not validated_recommendations:
            raise HTTPException(
                status_code=404,
                detail="No se pudieron generar recomendaciones válidas"
            )
                
        return validated_recommendations
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en endpoint de recomendaciones: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor al procesar recomendaciones"
        )
