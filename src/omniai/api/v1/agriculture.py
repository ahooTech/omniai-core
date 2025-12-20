from fastapi import APIRouter

router = APIRouter()

@router.get("/v1/agriculture")
async def health_check():
    return {"status": "ok"}