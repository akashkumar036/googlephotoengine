from __future__ import annotations
import hashlib, time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import structlog
from app.connectors.base import BaseConnector, NormalizedRecord
from app.config import get_settings

log = structlog.get_logger()
settings = get_settings()

try:
    import praw
    _PRAW_AVAILABLE = True
except ImportError:
    _PRAW_AVAILABLE = False

_SUBREDDITS = ["googlephotos", "iphone", "androidquestions", "techsupport", "ApplePhotos"]
_SEARCH_TERMS = [
    "find photo",
    "lost photo",
    "can't find",
    "cannot find photo",
    "photo retrieval",
    "searching for memory",
    "searching for photo",
]


class RedditConnector(BaseConnector):
    source_name = "reddit"
    rate_limit_per_minute = 60

    def __init__(self, reddit_client=None):
        self._reddit = reddit_client
        if self._reddit is None and _PRAW_AVAILABLE and settings.reddit_client_id and settings.reddit_client_id != "YOUR_REDDIT_CLIENT_ID":
            try:
                self._reddit = praw.Reddit(
                    client_id=settings.reddit_client_id,
                    client_secret=settings.reddit_client_secret,
                    user_agent=settings.reddit_user_agent,
                    read_only=True,
                )
            except Exception as e:
                log.warning("reddit_init_failed", error=str(e))

    def fetch(self, query="find photo", since=None, limit=100):
        if not _PRAW_AVAILABLE:
            raise RuntimeError("praw not installed")
        if not self._reddit:
            raise RuntimeError("REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET not configured")

        results = []
        search_terms = [query] if query else _SEARCH_TERMS
        per_term = max(5, limit // (len(_SUBREDDITS) * len(search_terms)))

        for subreddit_name in _SUBREDDITS:
            if len(results) >= limit:
                break
            try:
                subreddit = self._reddit.subreddit(subreddit_name)
            except Exception as e:
                log.warning("reddit_subreddit_error", subreddit=subreddit_name, error=str(e))
                continue

            for term in search_terms:
                if len(results) >= limit:
                    break
                try:
                    for sub in subreddit.search(term, limit=per_term, sort="new"):
                        if since:
                            sub_dt = datetime.fromtimestamp(sub.created_utc, tz=timezone.utc)
                            if sub_dt < since:
                                continue
                        results.append({
                            "_id": sub.id,
                            "type": "submission",
                            "subreddit": subreddit_name,
                            "title": sub.title,
                            "text": sub.selftext or sub.title,
                            "author": str(sub.author) if sub.author else None,
                            "url": "https://reddit.com" + getattr(sub, "permalink", f"/r/{subreddit_name}/comments/{sub.id}"),
                            "created_utc": sub.created_utc,
                            "score": sub.score,
                            "num_comments": sub.num_comments,
                            "search_term": term,
                        })

                        # Optionally fetch top-level comments for richer context (up to 2 per post)
                        if len(results) < limit and getattr(sub, "comments", None):
                            try:
                                sub.comments.replace_more(limit=0)
                                for c in sub.comments[:2]:
                                    if len(results) >= limit:
                                        break
                                    if c.body and len(c.body.split()) >= 8:
                                        results.append({
                                            "_id": f"{sub.id}_c_{c.id}",
                                            "type": "comment",
                                            "parent_id": sub.id,
                                            "subreddit": subreddit_name,
                                            "title": f"Re: {sub.title}",
                                            "text": c.body,
                                            "author": str(c.author) if c.author else None,
                                            "url": "https://reddit.com" + getattr(c, "permalink", getattr(sub, "permalink", "")),
                                            "created_utc": c.created_utc,
                                            "score": c.score,
                                            "num_comments": 0,
                                            "search_term": term,
                                        })
                            except Exception as ce:
                                log.debug("reddit_comments_error", error=str(ce))

                        time.sleep(60.0 / self.rate_limit_per_minute)
                except Exception as e:
                    log.warning("reddit_search_error", subreddit=subreddit_name, term=term, error=str(e))

        return results[:limit]

    def normalize(self, raw):
        raw_utc = raw.get("created_utc", 0)
        ts = datetime.fromtimestamp(raw_utc, tz=timezone.utc) if raw_utc else datetime.now(timezone.utc)
        a = raw.get("author")
        return NormalizedRecord(
            source_name="reddit",
            external_id="reddit_" + raw["_id"],
            url=raw.get("url"),
            author_hash=hashlib.sha256(a.encode()).hexdigest() if a else None,
            title=raw.get("title"),
            text=raw.get("text", "") or raw.get("title", ""),
            timestamp=ts,
            engagement={
                "upvotes": raw.get("score", 0),
                "comments": raw.get("num_comments", 0),
            },
            metadata={
                "subreddit": raw.get("subreddit"),
                "search_term": raw.get("search_term"),
                "type": raw.get("type", "submission"),
                "parent_id": raw.get("parent_id"),
            },
            is_demo=False,
        )
