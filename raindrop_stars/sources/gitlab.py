from collections.abc import Iterator

import requests

from ..models import StarredRepo
from .base import StarSource


class GitLabSource(StarSource):
    name = "gitlab"

    def __init__(self, token: str, base_url: str = "https://gitlab.com"):
        self.api = f"{base_url.rstrip('/')}/api/v4"
        self.session = requests.Session()
        self.session.headers.update({"PRIVATE-TOKEN": token})

    def iter_starred(self) -> Iterator[StarredRepo]:
        user_id = self._current_user_id()

        url = f"{self.api}/users/{user_id}/starred_projects"
        params = {"per_page": 100, "page": 1}

        while True:
            resp = self.session.get(url, params=params, timeout=30)
            resp.raise_for_status()

            for proj in resp.json():
                yield StarredRepo(
                    url=proj["web_url"],
                    title=proj["path_with_namespace"],
                    description=proj.get("description") or "",
                    source=self.name,
                )

            next_page = resp.headers.get("x-next-page")
            if not next_page:
                break
            params["page"] = int(next_page)

    def _current_user_id(self) -> int:
        resp = self.session.get(f"{self.api}/user", timeout=30)
        resp.raise_for_status()
        return resp.json()["id"]
