from fastapi import APIRouter, Query, status, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.scrap_steam import (
    ScrapSteamService,
    get_open_service,
    get_scrap_service,
)
from app.services.steam_api import SteamAPIService, get_steam_api_service
from app.schemas.game_details import GameDetails, SteamSearchResponse
from app.db.session import get_session

router = APIRouter(tags=["scrap"], prefix="/games")


@router.get(
    "/search",
    response_model=SteamSearchResponse,
)
async def search_games(
    query: str,
    limit: int = Query(
        default=10,
        ge=1,
        le=20,
    ),
    service: SteamAPIService = Depends(get_steam_api_service),
    session: AsyncSession = Depends(get_session)
):
    try:
        return await service.search_games(
            query,
            session,
            limit,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )

    except Exception:
        raise HTTPException(
            status_code=502,
            detail="Steam API is unavailable",
        )
    

@router.get("/details", response_model=GameDetails, status_code=status.HTTP_200_OK)
async def get_game_details(
    game_name: str,
    reviews_count: int = 3,
    scrap_steam_service: ScrapSteamService = Depends(get_scrap_service),
    session: AsyncSession = Depends(get_session)
):
    try:
        return await scrap_steam_service.get_game_info(game_name=game_name, reviews_count=reviews_count, session=session)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    # except Exception as e:
    #     raise HTTPException(status_code=500, detail=f"Помилка скрапінгу: {str(e)}")


@router.post("/game/open")
async def open_game(
    game_name: str,
    service: ScrapSteamService = Depends(get_open_service),
    session: AsyncSession = Depends(get_session)
):
    try:
        app_id, url = await service.open_game(game_name, session)

        return {
            "status": "success",
            "app_id": app_id,
            "url": url,
        }

    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e),
        )