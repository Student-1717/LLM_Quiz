# solver/browser.py
from playwright.async_api import async_playwright, TimeoutError as PTTimeout
import asyncio

async def render_page(url: str, timeout: int = 30000):
    """
    Fully hardened Playwright renderer for Render.
    Returns (html, text).
    """
    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                ]
            )
            context = await browser.new_context()
            page = await context.new_page()

            try:
                await page.goto(url, wait_until="networkidle", timeout=timeout)
            except PTTimeout:
                await page.goto(url, wait_until="load", timeout=timeout)

            html = await page.content()

            try:
                text = await page.inner_text("body")
            except Exception:
                text = await page.evaluate("() => document.body.innerText")

            await context.close()
            await browser.close()

            return html, text

    except Exception as e:
        raise RuntimeError(f"render_page error: {e}") from e
