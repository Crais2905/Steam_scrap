from typing import List

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession


from app.schemas.runs import RunResponse, RunRespBase
from app.db.session import get_session
from app.services.runs import RunsService, get_runs_service

router = APIRouter(tags=["runs"], prefix="/runs")



@router.get("/", response_model=List[RunRespBase], status_code=status.HTTP_200_OK)
async def get_runs(
    runs_service: RunsService = Depends(get_runs_service),
    offset: int = 0,
    limit: int = 10,
    session: AsyncSession = Depends(get_session)
):
    return await runs_service.get_runs(offset, limit, session)


@router.get("/{run_id}", response_model=RunResponse, status_code=status.HTTP_200_OK)
async def get_run_detailed(
    run_id: int,
    runs_service: RunsService = Depends(get_runs_service),
    session: AsyncSession = Depends(get_session)
):
    run = await runs_service.get_run_detailed(run_id, session)

    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found"
        )

    return run