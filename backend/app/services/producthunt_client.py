"""
Product Hunt GraphQL API client
────────────────────────────────
Discovers recently launched startups by topic/category.

How to get a token
──────────────────
1. Go to https://www.producthunt.com/v2/oauth/applications
2. Create a new application (any name, e.g. "VC Analyst")
3. Copy the "Developer Token" (no OAuth flow needed for read-only)
4. Add  PRODUCTHUNT_API_KEY=<token>  to backend/.env

Endpoint: POST https://api.producthunt.com/v2/api/graphql
Auth:     Authorization: Bearer <token>

Public functions
────────────────
  search_startups(keyword)  → list[CompanyProfile]

Falls back to empty list (not mock data) when key is absent so the
discovery agent can still use Crustdata / Unsiloed results.
"""

from __future__ import annotations

import httpx

from app.config.settings import settings
from app.services.crustdata_client import CompanyProfile, PersonProfile

_GRAPHQL_URL = "https://api.producthunt.com/v2/api/graphql"
_TIMEOUT = 15

# Map our sector keywords → Product Hunt topic slugs
_SECTOR_TO_TOPICS: dict[str, list[str]] = {
    "developer tools":      ["developer-tools", "productivity"],
    "devtools":             ["developer-tools"],
    "b2b saas":             ["saas", "productivity", "business-tools"],
    "saas":                 ["saas"],
    "infrastructure":       ["developer-tools", "cloud-computing"],
    "ai":                   ["artificial-intelligence"],
    "ai/ml":                ["artificial-intelligence", "machine-learning"],
    "fintech":              ["fintech", "payments"],
    "healthtech":           ["health-and-fitness", "medical"],
    "cybersecurity":        ["security"],
    "security":             ["security"],
    "marketplace":          ["marketplace"],
    "edtech":               ["education"],
    "climate tech":         ["sustainability"],
    "b2b":                  ["saas", "business-tools"],
}

_TOPIC_QUERY = """
query TopicPosts($slug: String!) {
  posts(first: 20, topic: $slug, order: VOTES) {
    edges {
      node {
        id
        name
        tagline
        description
        website
        votesCount
        topics {
          edges {
            node {
              name
            }
          }
        }
        makers {
          name
          headline
        }
      }
    }
  }
}
"""


_access_token: str | None = None


async def _get_access_token(http: httpx.AsyncClient) -> str | None:
    """Exchange API key + secret for an OAuth access token (client_credentials flow)."""
    global _access_token
    if _access_token:
        return _access_token
    try:
        resp = await http.post(
            "https://api.producthunt.com/v2/oauth/token",
            data={  # PH requires form-encoded, not JSON
                "client_id": settings.producthunt_api_key,
                "client_secret": settings.producthunt_api_secret,
                "grant_type": "client_credentials",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if resp.status_code == 200:
            _access_token = resp.json().get("access_token")
            print(f"[producthunt] obtained access token ok")
            return _access_token
        print(f"[producthunt] token exchange failed {resp.status_code}: {resp.text[:100]}")
    except Exception as exc:
        print(f"[producthunt] token exchange error: {exc}")
    return None


def _headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


async def search_startups(keyword: str) -> list[CompanyProfile]:
    """Search Product Hunt for startups matching a keyword / sector.

    Uses the posts search query directly with the keyword.
    Returns empty list when API key is absent or on error.
    """
    if not settings.producthunt_api_key:
        return []

    results: list[CompanyProfile] = []

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as http:
            token = await _get_access_token(http)
            if not token:
                print("[producthunt] no access token — skipping")
                return []

            topics = _keyword_to_topics(keyword)
            for slug in topics[:3]:
                print(f"[producthunt] querying topic='{slug}'")
                resp = await http.post(
                    _GRAPHQL_URL,
                    headers=_headers(token),
                    json={"query": _TOPIC_QUERY, "variables": {"slug": slug}},
                )
                print(f"[producthunt] topic '{slug}' status={resp.status_code}")
                if resp.status_code != 200:
                    continue
                body = resp.json()
                if body.get("errors"):
                    print(f"[producthunt] GraphQL errors: {body['errors'][0].get('message')}")
                    continue
                edges = (
                    (body.get("data") or {})
                    .get("posts", {})
                    .get("edges", [])
                )
                print(f"[producthunt] topic '{slug}' returned {len(edges)} posts")
                for edge in edges:
                        node = edge.get("node") or {}
                        if node:
                            results.append(_normalise_post(node))

    except Exception as exc:
        print(f"[producthunt] search_startups failed: {exc}")

    # Deduplicate by id, cap at 10
    seen: set[str] = set()
    unique: list[CompanyProfile] = []
    for c in results:
        if c.id not in seen:
            seen.add(c.id)
            unique.append(c)

    print(f"[producthunt] returning {len(unique[:10])} results for keyword='{keyword}'")
    return unique[:10]


# ── Normalisation ─────────────────────────────────────────────────────────────

def _normalise_post(post: dict) -> CompanyProfile:
    """Map a Product Hunt post node to CompanyProfile."""
    post_id = str(post.get("id") or "")
    name = post.get("name") or ""
    tagline = post.get("tagline") or ""
    description = post.get("description") or tagline
    website = post.get("website") or ""
    votes = post.get("votesCount") or 0

    # Extract topic names as signals
    topic_edges = (post.get("topics") or {}).get("edges") or []
    topic_names = [
        e["node"]["name"]
        for e in topic_edges
        if e.get("node", {}).get("name")
    ]

    signals: list[str] = topic_names[:3]
    if votes:
        signals.append(f"{votes} upvotes on Product Hunt")

    # Extract founders/makers
    founders: list[PersonProfile] = []
    for maker in (post.get("makers") or [])[:3]:
        founders.append(PersonProfile(
            name=maker.get("name") or "",
            title=maker.get("headline") or "Founder",
            background=maker.get("headline") or "",
        ))

    # Derive industry from topics
    industry = topic_names[0] if topic_names else "Technology"

    return CompanyProfile(
        id=f"ph_{post_id}",
        name=name,
        description=description,
        industry=industry,
        funding_stage="Seed",        # PH doesn't expose stage
        employee_count=0,
        website=website,
        linkedin_url="",
        geography="US",              # PH is US-skewed
        founded=0,
        founders=founders,
        signals=signals,
        _raw=post,
    )


def _keyword_to_topics(keyword: str) -> list[str]:
    """Map a sector keyword to Product Hunt topic slugs."""
    kw = keyword.lower().strip()
    if kw in _SECTOR_TO_TOPICS:
        return _SECTOR_TO_TOPICS[kw]
    for key, topics in _SECTOR_TO_TOPICS.items():
        if key in kw or kw in key:
            return topics
    # Generic fallback
    return ["artificial-intelligence", "saas", "developer-tools"]
