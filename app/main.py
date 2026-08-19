from contextlib import asynccontextmanager

from fastapi import FastAPI
from playwright.async_api import async_playwright

from app.routes.health import router as health_router
from app.routes.scrap import router as scrap_router
from app.routes.runs import router as runs_router
from app.services.scrap_steam import SteamScraperFactory


@asynccontextmanager
async def lifespan(app: FastAPI):
    playwright = await async_playwright().start()

    browser_args = [
        "--no-sandbox",
        "--disable-setuid-sandbox",
    ]

    headless_browser = await playwright.chromium.launch(
        headless=True,
        args=browser_args,
    )

    visible_browser = await playwright.chromium.launch(
        headless=False,
        args=browser_args,
    )

    app.state.scraper_factory = SteamScraperFactory(
        headless_browser=headless_browser,
        visible_browser=visible_browser,
    )

    app.state.playwright = playwright
    app.state.headless_browser = headless_browser
    app.state.visible_browser = visible_browser

    yield

    await app.state.headless_browser.close()
    await app.state.visible_browser.close()
    await app.state.playwright.stop()


app = FastAPI(lifespan=lifespan)

app.include_router(health_router)
app.include_router(scrap_router)
app.include_router(runs_router)