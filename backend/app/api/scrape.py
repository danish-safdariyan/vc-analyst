from datetime import datetime, timezone

from fastapi import APIRouter

from app.schemas.models import ScrapeRequest, ScrapeResponse
from app.services.browser_use_client import scrape

router = APIRouter(tags=["scrape"])


@router.post("/scrape", response_model=ScrapeResponse)
async def scrape_url(req: ScrapeRequest):
    content = await scrape(req.url, req.instruction)
    return ScrapeResponse(
        content=content,
        url=req.url,
        scraped_at=datetime.now(timezone.utc).isoformat(),
    )
