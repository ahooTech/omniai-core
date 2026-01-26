from fastapi import APIRouter
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

router = APIRouter()

@router.get("/metrics")
async def get_metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)