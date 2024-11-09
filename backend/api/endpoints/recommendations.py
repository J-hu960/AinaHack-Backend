from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import logging

from db.session import get_db_session
from app.recommender import ContentRecommender, Recomendacion

logger = logging.getLogger(__name__)
router = APIRouter()

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
        List[Recomendacion]: Recomendaciones personalizadas
    """
    try:
        logger.info(f"Solicitando recomendaciones para usuario {user_id}")
        
        recommender = ContentRecommender()
        recommendations = recommender.generate(user_id)
        
        if isinstance(recommendations, dict) and recommendations.get("error"):
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
                logger.error(f"Error validando recomendación: {str(e)}")
                continue
                
        return validated_recommendations
        
    except Exception as e:
        logger.error(f"Error en endpoint de recomendaciones: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error interno del servidor: {str(e)}"
        )
