"""Browser Use client for live web scraping with httpx fallback."""

import re

import httpx

# browser-use is an optional dependency
try:
    from browser_use import Agent as BrowserAgent
    from browser_use import Browser

    BROWSER_USE_AVAILABLE = True
except ImportError:
    BROWSER_USE_AVAILABLE = False


async def scrape(url: str, instruction: str = "Extract the main content") -> str:
    """
    Scrape a URL and return plain text content.
    Primary: browser-use (handles JS-heavy sites).
    Fallback: httpx + HTML stripping.
    """
    if BROWSER_USE_AVAILABLE:
        try:
            return await _scrape_with_browser_use(url, instruction)
        except Exception as exc:
            print(f"[browser_use] Failed, falling back to httpx: {exc}")

    return await _scrape_with_httpx(url)


async def _scrape_with_browser_use(url: str, instruction: str) -> str:
    """Use browser-use Agent to navigate and extract content."""
    from langchain_openai import ChatOpenAI  # browser-use peer dep

    from app.config.settings import settings

    llm = ChatOpenAI(
        base_url=settings.openrouter_base_url,
        api_key=settings.openrouter_api_key,
        model=settings.fast_model,
    )
    agent = BrowserAgent(
        task=f"{instruction}. URL: {url}",
        llm=llm,
    )
    result = await agent.run()
    return str(result)[:3000]  # cap at 3000 chars


async def _scrape_with_httpx(url: str) -> str:
    """Simple httpx GET + strip HTML tags."""
    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            resp = await client.get(
                url,
                headers={"User-Agent": "Mozilla/5.0 (VC Analyst Bot/1.0)"},
            )
            html = resp.text
            # Strip tags and collapse whitespace
            text = re.sub(r"<[^>]+>", " ", html)
            text = re.sub(r"\s+", " ", text).strip()
            return text[:3000]
    except Exception as exc:
        return f"[scrape failed: {exc}]"
