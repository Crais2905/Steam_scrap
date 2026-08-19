from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import insert, delete, update


from app.db.models import Runs 

class RunsRepo:
    async def write_to_db(self, data, session: AsyncSession):
        stmt = insert(Runs).values(data.model_dump()).returning(Runs)
        result = await session.execute(stmt)

        obj = result.scalar()

        await session.commit()

        await session.refresh(obj)
        return obj


    async def get_runs(
            self,
            session: AsyncSession,
            offset: int = 0,
            limit: int = 10,
    ):
        stmt = select(Runs).offset(offset).limit(limit)
        result = await session.scalars(stmt)
        return result.all()


    async def get_run_by_id(
        self,
        id: int,
        session: AsyncSession,
    ):
        stmt = select(Runs).where(Runs.id == id)
        return await session.scalar(stmt)
    