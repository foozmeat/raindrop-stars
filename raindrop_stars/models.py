from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class StarredRepo:
    url: str
    title: str
    description: str
    source: str                      # "github" | "gitlab" | "codeberg"
    starred_at: datetime | None = None
