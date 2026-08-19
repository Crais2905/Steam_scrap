from datetime import timezone, datetime
from fastapi import Request
from playwright.async_api import Browser
from sqlalchemy.ext.asyncio import AsyncSession

from app.scrapers.pw_scraper import PlaywrightSteamScraper
from app.repositories.runs import RunsRepo
from app.schemas.game_details import GameDetails
from app.schemas.runs import RunCreate, RunResponse
from app.enums.runs_enum import RunsStatus, MethodType


class ScrapSteamService:
    def __init__(self, scraper: PlaywrightSteamScraper, runs_repo: RunsRepo):
        self._scraper = scraper
        self._runs_repo = runs_repo

    async def get_game_info(self, game_name: str, session: AsyncSession, reviews_count: int = 3) -> GameDetails:
        started_at = datetime.now(timezone.utc)
        if not game_name.strip():
            raise ValueError("Game name is empty")

        try:
            result = await self._scraper.scrape_game_by_name(
                game_name,
                reviews_count,
            )

            run = RunCreate(
                method_type=MethodType.HEADLESS.value,
                request_data=str({
                    "game_name": game_name,
                    "reviews_count": reviews_count
                }),
                response_data=str(result.model_dump()),
                status=RunsStatus.COMPLETED.value,
                started_at=started_at,
                ended_at=datetime.now(timezone.utc)
            )

            await self._runs_repo.write_to_db(run, session)
            return result
        except Exception as e:
            run = RunCreate(
                    method_type=MethodType.HEADLESS.value,
                    request_data=str({
                        "game_name": game_name,
                        "reviews_count": reviews_count
                    }),
                    response_data=e,
                    status=RunsStatus.FAILED.value,
                    started_at=started_at,
                    ended_at=datetime.now(timezone.utc)
                )

            await self._runs_repo.write_to_db(run, session)
            raise Exception("Scraping failed")


    async def open_game(self, game_name: str, session: AsyncSession) -> tuple[str, str]:
        started_at = datetime.now(timezone.utc)

        try:
            if not game_name.strip():
                raise ValueError("Game name is empty")

            
            result = await self._scraper.open_game(game_name)

            run = RunCreate(
                method_type=MethodType.NON_HEADLESS.value,
                request_data=str({
                    "game_name": game_name,
                }),
                response_data=str({
                    "appid": result[0],
                    "url": result[1]
                }),
                status=RunsStatus.COMPLETED.value,
                started_at=started_at,
                ended_at=datetime.now(timezone.utc)
            )
            await self._runs_repo.write_to_db(run, session)

            return result
        except:
            run = RunCreate(
                method_type=MethodType.NON_HEADLESS.value,
                request_data=str({
                    "game_name": game_name
                }),
                response_data=str({
                    "appid": result[0],
                    "url": result[1]
                }),
                status=RunsStatus.FAILED.value,
                started_at=started_at,
                ended_at=datetime.now(timezone.utc)
            )

            await self._runs_repo.write_to_db(run, session)
            raise Exception("Scraping failed")


class SteamScraperFactory:
    def __init__(
        self,
        headless_browser: Browser,
        visible_browser: Browser,
    ):
        self._headless_browser = headless_browser
        self._visible_browser = visible_browser

    def create_scrape_service(self) -> ScrapSteamService:
        scraper = PlaywrightSteamScraper(
            browser=self._headless_browser,
        )
        return ScrapSteamService(scraper, RunsRepo())

    def create_open_service(self) -> ScrapSteamService:
        scraper = PlaywrightSteamScraper(
            browser=self._visible_browser,
        )
        return ScrapSteamService(scraper, RunsRepo())


def get_scrap_service(
    request: Request,
) -> ScrapSteamService:
    factory = request.app.state.scraper_factory
    return factory.create_scrape_service()


def get_open_service(
    request: Request,
) -> ScrapSteamService:
    factory = request.app.state.scraper_factory
    return factory.create_open_service()