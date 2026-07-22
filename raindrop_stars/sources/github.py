from collections.abc import Iterator
from datetime import datetime

import requests

from ..models import StarredRepo
from .base import StarSource

API = "https://api.github.com"


class GitHubSource(StarSource):
    name = "github"

    def __init__(self, token: str):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {token}",
                # star+json adds the "starred_at" timestamp to each item.
                "Accept": "application/vnd.github.star+json",
                "X-GitHub-Api-Version": "2022-11-28",
            }
        )

    def iter_starred(self) -> Iterator[StarredRepo]:
        url: str | None = f"{API}/user/starred"
        params: dict | None = {"per_page": 100, "sort": "created"}

        while url:
            resp = self.session.get(url, params=params, timeout=30)
            resp.raise_for_status()

            for item in resp.json():
                repo = item["repo"]
                yield StarredRepo(
                    url=repo["html_url"],
                    title=repo["full_name"],
                    description=repo.get("description") or "",
                    source=self.name,
                    starred_at=_parse(item.get("starred_at")),
                )

            # The "next" link already carries per_page/sort/page.
            url = resp.links.get("next", {}).get("url")
            params = None


def _parse(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None
