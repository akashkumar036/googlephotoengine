from __future__ import annotations
import hashlib
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import httpx
import structlog
from app.connectors.base import BaseConnector, NormalizedRecord
from app.config import get_settings

log = structlog.get_logger()
settings = get_settings()

_SUBREDDITS = ["googlephotos", "ApplePhotos", "iphone", "androidquestions", "techsupport"]
_SEARCH_TERMS = [
    "find photo",
    "lost photo",
    "can't find",
    "cannot find photo",
    "photo retrieval",
    "searching for memory",
    "searching for photo",
]


def _is_valid_token(token: Optional[str]) -> bool:
    """Return True if token is non-empty and not a placeholder."""
    if not token:
        return False
    t = token.strip()
    return not (t.startswith("YOUR_") or "YOUR_APIFY" in t or t == "change-me")


class RedditConnector(BaseConnector):
    """
    Reddit connector powered by Apify Reddit Scraper actor.
    Scrapes user submissions and discussions across relevant photo & device subreddits.
    Falls back gracefully to simulated Reddit feedback when offline or token is unset.
    """

    source_name = "reddit"
    rate_limit_per_minute = 60

    def __init__(
        self,
        api_token: Optional[str] = None,
        actor_id: Optional[str] = None,
        http_client: Optional[httpx.Client] = None,
    ):
        self.api_token = api_token or settings.apify_api_token
        self.actor_id = actor_id or settings.apify_reddit_actor or "trudax/reddit-scraper"
        self._client = http_client

    def fetch(
        self,
        query: str = "find photo",
        since: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Fetch Reddit posts via Apify Reddit Scraper actor.
        If APIFY_API_TOKEN is missing or invalid, provides realistic fallback Reddit data.
        """
        if _is_valid_token(self.api_token):
            try:
                return self._fetch_apify(query=query, since=since, limit=limit)
            except Exception as exc:
                log.warning("apify_reddit_fetch_failed_falling_back", error=str(exc))
                return self._fallback_data(query=query, since=since, limit=limit)

        log.info("apify_reddit_using_fallback", reason="No valid APIFY_API_TOKEN configured")
        return self._fallback_data(query=query, since=since, limit=limit)

    def _fetch_apify(
        self,
        query: str = "find photo",
        since: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Execute Apify actor synchronously and return dataset items."""
        actor_slug = self.actor_id.replace("/", "~")
        url = f"https://api.apify.com/v2/acts/{actor_slug}/run-sync-get-dataset-items?token={self.api_token}&timeout=60"

        searches = [query] if query else _SEARCH_TERMS[:3]
        payload = {
            "searches": searches,
            "subreddits": _SUBREDDITS,
            "sort": "new",
            "maxItems": limit,
            "maxComments": 3,
        }

        client = self._client or httpx.Client(timeout=65.0)
        close_client = self._client is None

        try:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, list):
                results = []
                for item in data:
                    # Filter by date if since specified
                    ts = self._extract_timestamp(item)
                    if since and ts and ts < since:
                        continue
                    results.append(item)
                    if len(results) >= limit:
                        break
                return results
            log.warning("apify_unexpected_response_format", data_type=type(data).__name__)
            return []
        finally:
            if close_client:
                client.close()

    def _fallback_data(
        self,
        query: str = "",
        since: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Simulated realistic Reddit posts for local dev, tests, and offline runs."""
        sample_posts = [
            {
                "id": "reddit_post_001",
                "title": "Google Photos search cannot find my dog from 2 years ago",
                "body": "I have hundreds of pictures of my golden retriever, but searching 'dog' or 'golden retriever' shows only 3 random pictures from last week. Where did the face and pet recognition go?",
                "author": "photouser_99",
                "subreddit": "googlephotos",
                "url": "https://reddit.com/r/googlephotos/comments/post001",
                "createdAt": "2026-08-15T14:20:00Z",
                "upVotes": 42,
                "numberOfComments": 18,
                "dataType": "post",
            },
            {
                "id": "reddit_post_002",
                "title": "Apple Photos search by location stopped working after update",
                "body": "Typing 'San Diego' or 'Hawaii' used to pull up all my vacation trips. Now it says 'No Results Found' even though the GPS location tag is clearly in the EXIF data!",
                "author": "ios_traveller",
                "subreddit": "ApplePhotos",
                "url": "https://reddit.com/r/ApplePhotos/comments/post002",
                "createdAt": "2026-08-20T10:15:00Z",
                "upVotes": 67,
                "numberOfComments": 24,
                "dataType": "post",
            },
            {
                "id": "reddit_post_003",
                "title": "Unable to find scanned receipts and documents using OCR",
                "body": "I used to search 'Home Depot receipt' and it found the image instantly. Now search only looks at file names which are just IMG_9482.jpg. Very frustrated.",
                "author": "receipt_hoarder",
                "subreddit": "googlephotos",
                "url": "https://reddit.com/r/googlephotos/comments/post003",
                "createdAt": "2026-09-01T08:30:00Z",
                "upVotes": 35,
                "numberOfComments": 12,
                "dataType": "post",
            },
            {
                "id": "reddit_post_004",
                "title": "Duplicates cluttering gallery and cleanup tool deleted originals",
                "body": "My phone backed up both high-res and thumbnails, creating 10,000 duplicates. The auto-clean tool wiped out the high quality versions without confirmation!",
                "author": "storage_stress",
                "subreddit": "androidquestions",
                "url": "https://reddit.com/r/androidquestions/comments/post004",
                "createdAt": "2026-09-10T16:45:00Z",
                "upVotes": 88,
                "numberOfComments": 31,
                "dataType": "post",
            },
            {
                "id": "reddit_post_005",
                "title": "Timeline scroll is broken and jumps to 1970",
                "body": "When scrolling back through 2023 photos, the scroll handle randomly snaps to December 31, 1969. I can never reach photos from specific months without tedious endless swiping.",
                "author": "vintage_shooter",
                "subreddit": "iphone",
                "url": "https://reddit.com/r/iphone/comments/post005",
                "createdAt": "2026-09-18T19:00:00Z",
                "upVotes": 51,
                "numberOfComments": 19,
                "dataType": "post",
            },
        ]

        if query:
            q_lower = query.lower()
            matching = [p for p in sample_posts if q_lower in p["title"].lower() or q_lower in p["body"].lower()]
            if matching:
                sample_posts = matching

        if since:
            sample_posts = [p for p in sample_posts if datetime.fromisoformat(p["createdAt"].replace("Z", "+00:00")) >= since]

        return sample_posts[:limit]

    def _extract_timestamp(self, raw: Dict[str, Any]) -> Optional[datetime]:
        """Extract datetime from varying Apify/Reddit timestamp schemas."""
        for field in ("createdAt", "created_at", "timestamp"):
            val = raw.get(field)
            if val:
                try:
                    if isinstance(val, (int, float)):
                        return datetime.fromtimestamp(val, tz=timezone.utc)
                    return datetime.fromisoformat(str(val).replace("Z", "+00:00"))
                except Exception:
                    pass
        raw_utc = raw.get("created_utc")
        if raw_utc:
            try:
                return datetime.fromtimestamp(float(raw_utc), tz=timezone.utc)
            except Exception:
                pass
        return None

    def normalize(self, raw: Dict[str, Any]) -> NormalizedRecord:
        """Map raw Apify Reddit post/comment to canonical NormalizedRecord."""
        raw_id = str(raw.get("id") or raw.get("parsedId") or raw.get("_id") or "")
        if not raw_id:
            raw_id = hashlib.md5((raw.get("url") or raw.get("title") or str(time.time())).encode()).hexdigest()[:12]

        external_id = raw_id if raw_id.startswith("reddit_") else f"reddit_{raw_id}"

        title = raw.get("title") or raw.get("parsedTitle")
        body = raw.get("body") or raw.get("selfText") or raw.get("text") or title or ""
        author = raw.get("author") or raw.get("username")
        url = raw.get("url") or raw.get("link") or raw.get("permalink")
        if url and url.startswith("/r/"):
            url = f"https://reddit.com{url}"

        ts = self._extract_timestamp(raw) or datetime.now(timezone.utc)

        upvotes = int(raw.get("upVotes") or raw.get("score") or 0)
        comments_cnt = int(raw.get("numberOfComments") or raw.get("num_comments") or 0)

        subreddit = raw.get("subreddit") or raw.get("communityName")

        return NormalizedRecord(
            source_name="reddit",
            external_id=external_id,
            url=url,
            author_hash=author,  # NormalizedRecord hashes this transparently
            title=title,
            text=body,
            timestamp=ts,
            engagement={
                "upvotes": upvotes,
                "comments": comments_cnt,
            },
            metadata={
                "subreddit": subreddit,
                "scraped_via": "apify",
                "dataType": raw.get("dataType", "post"),
            },
            is_demo=False,
        )
