from abc import ABC, abstractmethod
from collections.abc import Iterator

from ..models import StarredRepo


class StarSource(ABC):
    name: str

    @abstractmethod
    def iter_starred(self) -> Iterator[StarredRepo]:
        """Yield every repo the authenticated user has starred on this forge."""
