from datetime import datetime, timezone
import httpx
from decouple import config

from sqlalchemy.ext.asyncio import AsyncSession 

from app.schemas.game_details import SteamGame, SteamSearchResponse
from app.schemas.runs import RunCreate
from app.enums.runs_enum import RunsStatus, MethodType
from app.repositories.runs import RunsRepo

STEAM_API_URL = (
    "https://api.steampowered.com/"
    "IStoreService/GetAppList/v1/"
)


class SteamAPIService:
    def __init__(self, api_key: str, runs_repo: RunsRepo):
        self._api_key = api_key
        self._runs_repo = runs_repo

    async def search_games(
        self,
        query: str,
        session: AsyncSession,
        limit: int = 10
    ) -> SteamSearchResponse:
        started_at = datetime.now(timezone.utc)

        try:
            if not query.strip():
                raise ValueError("Search query is empty")

            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    STEAM_API_URL,
                    headers={
                        "x-webapi-key": self._api_key,
                    },
                    params={
                        "include_games": True,
                        "include_dlc": False,
                        "include_software": False,
                        "include_videos": False,
                        "include_hardware": False,
                        "max_results": 500,
                    },
                )

            response.raise_for_status()

            data = response.json()
            apps = data.get("response", {}).get("apps", [])
            query = query.strip().lower()

            games = [
                SteamGame(
                    app_id=app["appid"],
                    name=app["name"],
                    url=(
                        "https://store.steampowered.com/app/"
                        f"{app['appid']}/"
                    ),
                )
                for app in apps
                if query in app.get("name", "").lower()
            ]

            result = SteamSearchResponse(
                query=query,
                results=games[:limit]
            )

            run = RunCreate(
                method_type=MethodType.HTTP.value,
                request_data=str({
                    "query": query,
                    "limit": limit
                }),
                response_data=str(result.model_dump()),
                status=RunsStatus.COMPLETED.value,
                started_at=started_at,
                ended_at=datetime.now(timezone.utc)
            )
            await self._runs_repo.write_to_db(run, session)

            return result
        except:
            run = RunCreate(
                method_type=MethodType.HTTP.value,
                request_data=str({
                    "query": query,
                    "limit": limit
                }),
                response_data=str(result.model_dump()),
                status=RunsStatus.FAILED.value,
                started_at=started_at,
                ended_at=datetime.now(timezone.utc)
            )

            await self._runs_repo.write_to_db(run, session)
            raise Exception("Scraping failed")


def get_steam_api_service() -> SteamAPIService:
    return SteamAPIService(
        api_key=config("STEAM_API_KEY"),
        runs_repo=RunsRepo()
    )