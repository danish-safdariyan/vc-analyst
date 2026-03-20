"""
Unsiloed AI client — document parsing
──────────────────────────────────────
Unsiloed AI parses unstructured documents (PDFs, images) into structured JSON.

Primary use-case in vc-analyst-ai
───────────────────────────────────
Parse pitch decks uploaded by the user to extract:
  - Company name, description, problem/solution
  - Traction metrics (ARR, customers, growth)
  - Team bios
  - Market size claims
  - Funding ask

This structured output feeds directly into the thesis match and drift agents
as a richer signal source than a text thesis alone.

API
───
  POST https://prod.visionapi.unsiloed.ai/parse
  Headers: api-key: <key>, Content-Type: multipart/form-data
  Body:    file=<pdf_bytes>
  Returns: { "chunks": [ { "text": str, "type": str, ... } ] }

Public functions
────────────────
  parse_document(file_bytes, filename)  → ParsedDocument
  extract_startup_signals(chunks)       → dict  (key facts as plain dict)
"""

from __future__ import annotations

import io
from dataclasses import dataclass, field

import httpx

from app.config.settings import settings

_PARSE_URL = "https://prod.visionapi.unsiloed.ai/parse"
_TIMEOUT = 30  # document parsing can be slow


# ── Result schemas ────────────────────────────────────────────────────────────

@dataclass
class DocumentChunk:
    text: str
    chunk_type: str = ""   # e.g. "title", "paragraph", "table", "list"
    page: int = 0


@dataclass
class ParsedDocument:
    filename: str
    chunks: list[DocumentChunk] = field(default_factory=list)
    full_text: str = ""
    # Extracted key facts
    company_name: str = ""
    description: str = ""
    traction: list[str] = field(default_factory=list)
    team: list[str] = field(default_factory=list)
    market_size: str = ""
    funding_ask: str = ""


# ── Public API ────────────────────────────────────────────────────────────────

async def parse_document(file_bytes: bytes, filename: str = "document.pdf") -> ParsedDocument:
    """Send a file to Unsiloed AI and return structured chunks.

    Returns an empty ParsedDocument on failure rather than raising.
    """
    if not settings.unsiloed_api_key:
        print("[unsiloed] no API key — skipping document parse")
        return ParsedDocument(filename=filename)

    try:
        print(f"[unsiloed] parsing document '{filename}' ({len(file_bytes)} bytes)")
        async with httpx.AsyncClient(timeout=_TIMEOUT) as http:
            resp = await http.post(
                _PARSE_URL,
                headers={"api-key": settings.unsiloed_api_key},
                files={"file": (filename, io.BytesIO(file_bytes), "application/pdf")},
            )
            print(f"[unsiloed] response status={resp.status_code}")
            resp.raise_for_status()
            body = resp.json()

        raw_chunks = body.get("chunks") or body.get("elements") or []
        chunks = [
            DocumentChunk(
                text=c.get("text") or c.get("content") or "",
                chunk_type=c.get("type") or c.get("element_type") or "",
                page=c.get("page") or c.get("page_number") or 0,
            )
            for c in raw_chunks
            if (c.get("text") or c.get("content") or "").strip()
        ]

        full_text = "\n".join(c.text for c in chunks)
        doc = ParsedDocument(filename=filename, chunks=chunks, full_text=full_text)
        _enrich(doc)
        print(f"[unsiloed] parsed {len(chunks)} chunks, extracted signals")
        return doc

    except httpx.HTTPStatusError as exc:
        print(f"[unsiloed] HTTP {exc.response.status_code} — {exc.response.text[:200]}")
        return ParsedDocument(filename=filename)
    except Exception as exc:
        print(f"[unsiloed] parse_document failed: {exc}")
        return ParsedDocument(filename=filename)


def extract_startup_signals(doc: ParsedDocument) -> dict:
    """Return a plain dict of key startup facts for use as extra signals."""
    signals: list[str] = []

    if doc.company_name:
        signals.append(f"Company: {doc.company_name}")
    if doc.description:
        signals.append(f"What they do: {doc.description}")
    signals.extend(doc.traction)
    signals.extend(doc.team)
    if doc.market_size:
        signals.append(f"Market: {doc.market_size}")
    if doc.funding_ask:
        signals.append(f"Raising: {doc.funding_ask}")

    return {
        "company_name": doc.company_name,
        "description": doc.description,
        "traction": doc.traction,
        "team": doc.team,
        "market_size": doc.market_size,
        "funding_ask": doc.funding_ask,
        "signals": signals,
        "full_text": doc.full_text[:2000],  # first 2K chars as context
    }


# ── Internal enrichment ───────────────────────────────────────────────────────

def _enrich(doc: ParsedDocument) -> None:
    """Heuristically extract key facts from parsed chunks."""
    text_lower = doc.full_text.lower()
    lines = [c.text.strip() for c in doc.chunks if c.text.strip()]

    # Company name — often the first title chunk
    for chunk in doc.chunks:
        if chunk.chunk_type in ("title", "heading") and chunk.text.strip():
            doc.company_name = chunk.text.strip()
            break

    # Description — first non-trivial paragraph
    for chunk in doc.chunks:
        if chunk.chunk_type in ("paragraph", "") and len(chunk.text) > 40:
            doc.description = chunk.text[:300]
            break

    # Traction signals — lines containing ARR, MRR, customers, growth keywords
    traction_keywords = ["arr", "mrr", "revenue", "customers", "users", "growth",
                         "yoy", "retention", "nrr", "churn", "raised", "funding"]
    for line in lines:
        ll = line.lower()
        if any(kw in ll for kw in traction_keywords) and len(line) < 200:
            doc.traction.append(line)
        if len(doc.traction) >= 5:
            break

    # Team — lines mentioning founder titles
    team_keywords = ["founder", "ceo", "cto", "cpo", "co-founder", "vp"]
    for line in lines:
        ll = line.lower()
        if any(kw in ll for kw in team_keywords) and len(line) < 150:
            doc.team.append(line)
        if len(doc.team) >= 3:
            break

    # Market size — lines with "$" and "billion" or "market"
    for line in lines:
        ll = line.lower()
        if ("$" in ll or "billion" in ll or "tam" in ll) and "market" in ll:
            doc.market_size = line[:200]
            break

    # Funding ask — lines with "raising" or "round"
    for line in lines:
        ll = line.lower()
        if ("raising" in ll or "round" in ll or "seeking" in ll) and "$" in ll:
            doc.funding_ask = line[:150]
            break
