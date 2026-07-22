from .. import config
from .base import StarSource
from .codeberg import CodebergSource
from .github import GitHubSource
from .gitlab import GitLabSource


def build_sources() -> list[StarSource]:
    """Return one source per configured token; skip forges with no token."""
    sources: list[StarSource] = []

    if config.GH_STAR_TOKEN:
        sources.append(GitHubSource(config.GH_STAR_TOKEN))

    if config.GITLAB_TOKEN:
        sources.append(GitLabSource(config.GITLAB_TOKEN, config.GITLAB_URL))

    if config.CODEBERG_TOKEN:
        sources.append(CodebergSource(config.CODEBERG_TOKEN, config.CODEBERG_URL))

    return sources
