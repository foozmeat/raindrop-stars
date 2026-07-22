from .. import config
from .base import StarSource
from .codeberg import CodebergSource
from .github import GitHubSource
from .gitlab import GitLabSource

# Every tag this tool applies -- used by cleanup to find bookmarks it imported,
# regardless of which tokens happen to be configured on a given run.
ALL_SOURCE_NAMES = [GitHubSource.name, GitLabSource.name, CodebergSource.name]


def build_sources() -> list[StarSource]:
    """Return one source per configured token; skip forges with no token."""
    sources: list[StarSource] = []

    if config.GITHUB_STAR_TOKEN:
        sources.append(GitHubSource(config.GITHUB_STAR_TOKEN))

    if config.GITLAB_TOKEN:
        sources.append(GitLabSource(config.GITLAB_TOKEN, config.GITLAB_URL))

    if config.CODEBERG_TOKEN:
        sources.append(CodebergSource(config.CODEBERG_TOKEN, config.CODEBERG_URL))

    return sources
