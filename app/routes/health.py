from fastapi import APIRouter, status


router = APIRouter(tags=["health"], prefix="/health")


@router.get("/", status_code=status.HTTP_200_OK)
async def health_check() -> dict:
    return {
        "status": "ok"
    }