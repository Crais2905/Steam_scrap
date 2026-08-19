from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession


from app.repositories.runs import RunsRepo

class RunsService:
    def __init__(self, runs_repo: RunsRepo):
        self._runs_repo = runs_repo


    async def get_runs(self, offset: int, limit: int, session: AsyncSession):
        return await self._runs_repo.get_runs(session, offset, limit) 


    async def get_run_detailed(self, run_id: int, session: AsyncSession):
        return await self._runs_repo.get_run_by_id(run_id, session)



def get_runs_service(runs_repo: RunsRepo = Depends(RunsRepo)) -> RunsService:
    return RunsService(runs_repo)