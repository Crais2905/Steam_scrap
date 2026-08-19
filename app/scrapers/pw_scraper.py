import re
from typing import List
from decouple import config

from playwright.async_api import (
    Browser,
    BrowserContext,
    Locator,
    Page,
)

from app.schemas.game_details import GameDetails, Review


class PlaywrightSteamScraper:
    def __init__(self, browser: Browser):
        self._browser = browser

    async def scrape_game_by_name(
        self,
        game_name: str,
        reviews_count: int = 3,
    ) -> GameDetails:
        context = await self._create_context()

        try:
            page = await context.new_page()
            page.set_default_timeout(20_000)

            game_url, app_id = await self._find_game(
                page,
                game_name,
            )

            await page.goto(
                game_url,
                wait_until="domcontentloaded",
            )
            await page.wait_for_timeout(1500)

            game_info = await self._parse_game_info(page)
            reviews = await self._parse_reviews(
                page,
                reviews_count,
            )

            return GameDetails(
                app_id=app_id,
                url=game_url,
                reviews=reviews,
                **game_info,
            )

        finally:
            await context.close()

    async def open_game(
        self,
        game_name: str,
    ) -> tuple[str, str]:
        page = await self._browser.new_page()
        page.set_default_timeout(20_000)

        game_url, app_id = await self._find_game(
            page,
            game_name,
        )

        await page.goto(
            game_url,
            wait_until="domcontentloaded",
        )

        return app_id, game_url

    async def _create_context(self) -> BrowserContext:
        context = await self._browser.new_context(
            locale="uk-UA",
            viewport={"width": 1920, "height": 1080},
            extra_http_headers={
                "Accept-Language": config("Accept-Language")
            },
        )

        await context.add_cookies([
            {
                "name": "steamCountry",
                "value": "UA%7C00000000000000000000000000000000",
                "domain": ".store.steampowered.com",
                "path": "/",
            },
            {
                "name": "wants_mature_content",
                "value": "1",
                "domain": ".store.steampowered.com",
                "path": "/",
            },
            {
                "name": "birthtime",
                "value": "568028401",
                "domain": ".store.steampowered.com",
                "path": "/",
            },
        ])

        return context

    async def _find_game(
        self,
        page: Page,
        game_name: str,
    ) -> tuple[str, str]:
        search_url = (
            "https://store.steampowered.com/search/"
            f"?term={game_name}&cc=ua&l=ukrainian"
        )

        await page.goto(
            search_url,
            wait_until="domcontentloaded",
        )

        result = page.locator(
            "#search_resultsRows a"
        ).first

        if await result.count() == 0:
            raise ValueError(
                f"Game '{game_name}' not found."
            )

        game_url = await result.get_attribute("href")

        if not game_url:
            raise ValueError(
                "Cant get a game url"
            )

        game_url = game_url.split("?")[0]

        match = re.search(
            r"/app/(\d+)",
            game_url,
        )

        if not match:
            raise ValueError(
                "Cant get a game app_id"
            )

        return (
            f"{game_url}?cc=ua&l=ukrainian",
            match.group(1),
        )

    async def _parse_game_info(
        self,
        page: Page,
    ) -> dict:
        title_elem = page.locator("#appHubAppName")

        title = (
            await title_elem.inner_text()
            if await title_elem.count()
            else "Unknown Title"
        )

        devs = page.locator(".dev_row .summary")

        developer = (
            await devs.nth(0).inner_text()
            if await devs.count() > 0
            else "N/A"
        )

        publisher = (
            await devs.nth(1).inner_text()
            if await devs.count() > 1
            else "N/A"
        )

        date_elem = page.locator(".date")

        release_date = (
            await date_elem.inner_text()
            if await date_elem.count()
            else "N/A"
        )

        price_elem = page.locator(
            ".game_purchase_price, .discount_final_price"
        ).first

        price = (
            await price_elem.inner_text()
            if await price_elem.count()
            else "Free"
        )

        desc_elem = page.locator(
            ".game_description_snippet"
        )

        short_description = (
            await desc_elem.inner_text()
            if await desc_elem.count()
            else ""
        )

        summary_elem = page.locator(
            ".game_review_summary"
        ).first

        overall_summary = (
            await summary_elem.inner_text()
            if await summary_elem.count()
            else "N/A"
        )

        return {
            "title": title.strip(),
            "developer": developer.strip(),
            "publisher": publisher.strip(),
            "release_date": release_date.strip(),
            "price": price.strip(),
            "short_description": short_description.strip(),
            "overall_review_summary": overall_summary.strip(),
        }

    async def _parse_reviews(
        self,
        page: Page,
        reviews_count: int,
    ) -> List[Review]:
        review_links = page.locator(
            "a[href*='/recommended/']"
        )

        for _ in range(15):
            if await review_links.count() >= reviews_count:
                break

            await page.mouse.wheel(0, 700)
            await page.wait_for_timeout(500)

        cards_count = await review_links.count()

        if cards_count == 0:
            raise ValueError(
                "Reviews not found."
            )

        reviews = []

        for i in range(cards_count):
            if len(reviews) >= reviews_count:
                break

            card = review_links.nth(i).locator(
                "xpath=ancestor::div[contains(@class, 'Panel')][1]"
            )

            if await card.count() == 0:
                continue

            review = await self._parse_review(card)

            if review:
                reviews.append(review)

        return reviews

    async def _parse_review(
        self,
        card: Locator,
    ) -> Review | None:
        text = await self._get_review_text(card)

        if not text:
            return None

        recommendation = card.locator(
            "div._17lxcLR8FnXBii5ZgrKZCf"
        )

        recommendation_text = (
            await recommendation.inner_text()
            if await recommendation.count()
            else ""
        )

        date_elem = card.locator(
            "div._36PINioDf9qx6L5QCpuW3l"
        )

        posted_date_raw = (
            await date_elem.inner_text()
            if await date_elem.count()
            else ""
        )
        posted_date = self._normalize_posted_date(posted_date_raw)

        playtime_elem = card.locator(
            "div._1N9XZTVu3iXgXmyuKwSF4E"
        )

        playtime = (
            await playtime_elem.inner_text()
            if await playtime_elem.count()
            else None
        )

        return Review(
            text=text,
            is_positive="Рекомендовано" in recommendation_text,
            posted_date=posted_date.strip(),
            playtime=playtime.strip() if playtime else None,
        )

    @staticmethod
    def _normalize_posted_date(raw: str) -> str:
        if not raw:
            return ""

        text = raw.strip()

        text = re.sub(
            r"^додано:?\s*",
            "",
            text,
            flags=re.IGNORECASE,
        )

        return text.lower().strip()

    @staticmethod
    async def _get_review_text(card: Locator) -> str:
        selectors = [
            "div._3cl9mzgp8WIVuj1VCw9yi0",
            "[data-testid='review-text']",
        ]

        for selector in selectors:
            element = card.locator(selector)

            if await element.count():
                text = await element.last.inner_text()

                if text.strip():
                    return text.strip()

        return ""