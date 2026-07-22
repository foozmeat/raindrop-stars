from collections.abc import Iterator, Sequence

import requests

from .models import StarredRepo

API = "https://api.raindrop.io/rest/v1"

# Raindrop's bulk endpoints accept at most 100 items per request.
BATCH_SIZE = 100

# Deleting raindrops from this pseudo-collection removes them permanently
# instead of moving them to Trash.
TRASH_ID = -99


class RaindropClient:
    def __init__(self, token: str):
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {token}"})

    def get_or_create_collection(self, title: str) -> int:
        resp = self.session.get(f"{API}/collections", timeout=30)
        resp.raise_for_status()
        for c in resp.json()["items"]:
            if c["title"] == title:
                return c["_id"]

        resp = self.session.post(f"{API}/collection", json={"title": title}, timeout=30)
        resp.raise_for_status()
        return resp.json()["item"]["_id"]

    def iter_items(self, collection_id: int) -> Iterator[dict]:
        page = 0
        while True:
            resp = self.session.get(
                f"{API}/raindrops/{collection_id}",
                params={"perpage": 50, "page": page},
                timeout=30,
            )
            resp.raise_for_status()

            items = resp.json()["items"]
            if not items:
                break

            yield from items
            page += 1

    def existing_links(self, collection_id: int) -> set[str]:
        """Every bookmark URL already in the collection -- used for dedup."""
        return {item["link"] for item in self.iter_items(collection_id)}

    def create_many(self, collection_id: int, repos: Sequence[StarredRepo]) -> None:
        for batch in _chunks(repos, BATCH_SIZE):
            items = [
                {
                    "link": r.url,
                    "title": r.title,
                    "excerpt": r.description,
                    "collection": {"$id": collection_id},
                    "tags": [r.source],
                    "pleaseParse": {},
                }
                for r in batch
            ]
            resp = self.session.post(
                f"{API}/raindrops", json={"items": items}, timeout=60
            )
            resp.raise_for_status()

    def delete_permanently(self, collection_id: int, ids: Sequence[int]) -> None:
        """Move the given raindrops to Trash, then purge them from it."""
        for endpoint in (collection_id, TRASH_ID):
            for batch in _chunks(ids, BATCH_SIZE):
                resp = self.session.delete(
                    f"{API}/raindrops/{endpoint}",
                    json={"ids": list(batch)},
                    timeout=60,
                )
                resp.raise_for_status()


def _chunks(items: Sequence, size: int) -> Iterator[Sequence]:
    for start in range(0, len(items), size):
        yield items[start : start + size]
