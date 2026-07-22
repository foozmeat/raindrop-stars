from decouple import config

RAINDROP_TOKEN = config("RAINDROP_TOKEN")
COLLECTION_NAME = config("COLLECTION_NAME", default="starred-repos")

GH_STAR_TOKEN = config("GH_STAR_TOKEN", default="")

GITLAB_TOKEN = config("GITLAB_TOKEN", default="")
GITLAB_URL = config("GITLAB_URL", default="https://gitlab.com")

CODEBERG_TOKEN = config("CODEBERG_TOKEN", default="")
CODEBERG_URL = config("CODEBERG_URL", default="https://codeberg.org")

# Optional healthchecks.io ping URL; pinged when a sync completes successfully.
HEALTHCHECK_URL = config("HEALTHCHECK_URL", default="")
