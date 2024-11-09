from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict
import logging

from db.session import get_db_session
from app.recommender import ContentRecommender

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/recommendations/{user_id}", response_model=Dict)
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
        Dict: Recomendaciones personalizadas
    """
    try:
        logger.info(f"Solicitando recomendaciones para usuario {user_id}")
        
        # Usar la ruta de base de datos desde la configuración
        recommender = ContentRecommender()
        recommendations = recommender.generate(user_id)
        
        if recommendations.get("error"):
            raise HTTPException(
                status_code=404, 
                detail=recommendations.get("error")
            )
            
        return recommendations
        
    except Exception as e:
        logger.error(f"Error en endpoint de recomendaciones: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error interno del servidor: {str(e)}"
        )
