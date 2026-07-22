# raindrop-stars

> This repo is 100% vibe-coded. YMMV

Sync the repositories you've starred on **GitHub**, **GitLab**, and **Codeberg**
into a single [Raindrop.io](https://raindrop.io) collection. Each bookmark is
tagged with `starred-import` (a marker so imports can be cleaned up precisely)
and its source forge (`github` / `gitlab` / `codeberg`).

There is no hosted (IFTTT/Zapier) path for this: none of those services offer a
"the authenticated user starred a repo" trigger, and GitHub emits no event when
*you* star something. So this polls each forge's "my starred repos" API on a
schedule and adds anything new to Raindrop.

## How it works

1. Ask each configured forge for the full list of repos you've starred.
2. Fetch the URLs already in the target Raindrop collection.
3. Create bookmarks for the ones that aren't there yet (deduped by URL).

Because it dedupes by URL, the first run backfills all your existing stars and
every later run adds only what's new — running it repeatedly is safe.

## Setup

Requires [uv](https://docs.astral.sh/uv/).

```sh
uv sync
cp .env.example .env      # then fill in tokens
uv run python -m raindrop_stars
```

Configure at least one source. A forge is only queried when its token is set,
so GitHub-only (or any subset) works fine. See `.env.example` for every option.

### Tokens

- **Raindrop** — Settings → Integrations → create an app → copy the *test token*.
- **GitHub** — a PAT with read access to your stars. Store it as
  `GH_STAR_TOKEN` — GitHub Actions rejects secret names starting with `GITHUB_`.
- **GitLab** — a PAT with the `read_api` scope.
- **Codeberg** — an access token with **both** `read:user` and `read:repository`
  (the `/user/starred` endpoint requires both).

## Cleaning up imported bookmarks

To **permanently** delete every bookmark this tool imported (matched by the
`starred-import` marker tag, so hand-added bookmarks are left alone):

```sh
uv run python -m raindrop_stars cleanup         # dry run: reports the count
uv run python -m raindrop_stars cleanup --yes   # actually deletes
```

Deletion is permanent — the bookmarks are moved to Trash and then purged from
it, so they are **not** recoverable. Without `--yes` it only reports how many
would be removed.

Note: cleanup does not stop future syncs. Any repo you still have starred will
be re-imported on the next run — to keep the collection empty, unstar the repos
(or disable the scheduled workflow).

## Automated runs (GitHub Actions)

`.github/workflows/sync.yml` runs the sync daily (and on demand via
*workflow_dispatch*). Add each token under **Settings → Secrets and variables →
Actions**. Secrets are encrypted, invisible in the repo, and masked in logs — so
this repo is safe to keep public.

The script logs **counts only**, never repo names or URLs, so nothing sensitive
lands in the world-readable Actions logs of a public repo.
