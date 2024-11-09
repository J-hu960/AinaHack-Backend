from pydantic import BaseModel
from typing import Dict, Any, Optional

class Task(BaseModel):
    description: str
    expected_output: Dict[str, Any]  # Este campo es requerido y está faltando
    
    class Config:
        arbitrary_types_allowed = True
