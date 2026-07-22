# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A polling sync that copies the repos you've starred on GitHub, GitLab, and
Codeberg into a single Raindrop.io collection (default: `starred-repos`), one
bookmark per repo, tagged with its source forge.

There is deliberately no IFTTT/Zapier/webhook path: no such service exposes a
"the authenticated user starred a repo" trigger, and GitHub emits no event when
*you* star a repo (its star webhook fires only for repos you own). Polling each
forge's "list my starred repos" API is the only reliable approach — keep that in
mind before proposing a "simpler" event-driven design.

## Commands

```sh
uv sync                                       # install deps into .venv
uv run python -m raindrop_stars               # run the sync (default command)
uv run python -m raindrop_stars cleanup       # dry-run: count tool-imported bookmarks
uv run python -m raindrop_stars cleanup --yes # permanently delete them
```

There is no test suite yet. `python-decouple` reads config from a git-ignored
`.env` locally; on GitHub Actions the same variables arrive as repository
secrets, so there is no code branch between the two environments.

## Architecture

Sources fan in, one Raindrop sink writes out:

- `raindrop_stars/sources/base.py` — `StarSource` ABC: `iter_starred()` yields
  `StarredRepo` objects. Add a forge by implementing this and registering it in
  `sources/__init__.py:build_sources()`.
- `raindrop_stars/sources/{github,gitlab,codeberg}.py` — one per forge. Each owns
  its own auth header, pagination style, and field mapping (the three APIs differ:
  GitHub uses Link-header pagination + the `star+json` media type for
  `starred_at`; GitLab uses the `x-next-page` header and needs the user id first;
  Codeberg/Forgejo uses `page`/`limit` and stops on an empty page).
- `raindrop_stars/raindrop.py` — `RaindropClient`: resolve/create the collection,
  read existing links for dedup, bulk-create new bookmarks (≤100 per request).
- `raindrop_stars/__main__.py` — argparse entry point. Default command is `sync`
  (build sources, dedup against the collection's existing URLs, bulk-create the
  rest). The `cleanup` command permanently deletes bookmarks this tool imported,
  identified by the `MANAGED_TAG` marker; it requires `--yes` and deletes via
  `RaindropClient.delete_permanently` (move to Trash, then purge from `-99`).

Each bookmark is tagged with `MANAGED_TAG` (`starred-import`, defined in
`raindrop_stars/__init__.py`) and its forge (`github`/`gitlab`/`codeberg`).

Key invariants:

- **Dedup is by repo URL**, which is what makes the job idempotent (backfill on
  first run, incremental after). Preserve this when changing the sink.
- **`MANAGED_TAG` is the cleanup key.** Match on it, not the forge tags, so
  hand-added bookmarks (which may share a forge name as a tag) are never deleted.
- **A source is active only if its token is set** (`build_sources()`), so any
  subset of forges works. Don't make a missing token fatal.
- **Logging is counts-only, never repo names/URLs.** The repo is intended to be
  public, and Actions logs on a public repo are world-readable. Keep starred-repo
  details out of logs.
- **Sources are isolated.** `sync()` wraps each source; a failing forge (bad
  token, API error) is logged and skipped so the others still sync. The run
  still `raise SystemExit`s at the end if any source failed, so CI goes red.

## Conventions

- Tokens come from env via `python-decouple` (`config.py`); never hard-code them.
  The GitHub token variable is `GH_STAR_TOKEN` — GitHub Actions rejects secret
  names starting with the reserved `GITHUB_` prefix.
- `[tool.uv] package = false` — this is an app, not a packaged library; run it as
  a module (`python -m raindrop_stars`).
