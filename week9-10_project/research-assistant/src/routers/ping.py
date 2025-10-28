from fastapi import APIRouter
from ..config import get_settings
router = APIRouter()

@router.get("/ping")
def ping():
    return {"ping": "pong"}
