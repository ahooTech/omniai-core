from fastapi import APIRouter

router = APIRouter()

@router.get("/agriculture")
async def health_check():
    return {"status": "ok"}