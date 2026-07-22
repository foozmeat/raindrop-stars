from collections.abc import Iterator

import requests

from ..models import StarredRepo
from .base import StarSource


class CodebergSource(StarSource):
    """Codeberg runs Forgejo, whose API is Gitea-compatible."""

    name = "codeberg"

    def __init__(self, token: str, base_url: str = "https://codeberg.org"):
        self.api = f"{base_url.rstrip('/')}/api/v1"
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"token {token}"})

    def iter_starred(self) -> Iterator[StarredRepo]:
        page = 1

        while True:
            resp = self.session.get(
                f"{self.api}/user/starred",
                params={"limit": 50, "page": page},
                timeout=30,
            )
            resp.raise_for_status()

            repos = resp.json()
            if not repos:
                break

            for repo in repos:
                yield StarredRepo(
                    url=repo["html_url"],
                    title=repo["full_name"],
                    description=repo.get("description") or "",
                    source=self.name,
                )

            page += 1
