import argparse
import logging

import requests

from . import MANAGED_TAG, config
from .raindrop import RaindropClient
from .sources import build_sources

log = logging.getLogger("raindrop_stars")


def ping_healthcheck() -> None:
    if not config.HEALTHCHECK_URL:
        return
    try:
        requests.get(config.HEALTHCHECK_URL, timeout=10)
    except requests.RequestException as exc:
        log.warning("Healthcheck ping failed: %s", exc)


def sync() -> None:
    sources = build_sources()
    if not sources:
        log.error("No source tokens configured; nothing to do.")
        return

    client = RaindropClient(config.RAINDROP_TOKEN)
    collection_id = client.get_or_create_collection(config.COLLECTION_NAME)
    seen = client.existing_links(collection_id)

    # Each forge is isolated: one failing source logs a warning and is skipped,
    # so the others still sync. Log counts only -- repo names/URLs are kept out
    # of the (public) logs.
    new_repos = []
    failed = []
    for source in sources:
        try:
            found = list(source.iter_starred())
        except Exception as exc:
            failed.append(source.name)
            log.warning("%s: skipped -- %s", source.name, exc)
            continue

        count = 0
        for repo in found:
            if repo.url in seen:
                continue
            seen.add(repo.url)
            new_repos.append(repo)
            count += 1
        log.info("%s: %d new", source.name, count)

    if new_repos:
        client.create_many(collection_id, new_repos)

    log.info(
        "Done: %d new bookmark(s) added to '%s'.",
        len(new_repos),
        config.COLLECTION_NAME,
    )

    if failed:
        raise SystemExit(f"Sources failed: {', '.join(failed)}")

    ping_healthcheck()


def cleanup(assume_yes: bool) -> None:
    client = RaindropClient(config.RAINDROP_TOKEN)
    collection_id = client.get_or_create_collection(config.COLLECTION_NAME)

    ids = [
        item["_id"]
        for item in client.iter_items(collection_id)
        if MANAGED_TAG in (item.get("tags") or [])
    ]

    if not ids:
        log.info("Nothing imported by this tool to clean up in '%s'.", config.COLLECTION_NAME)
        return

    if not assume_yes:
        log.error(
            "Would permanently delete %d imported bookmark(s) from '%s'. "
            "Re-run with --yes to confirm.",
            len(ids),
            config.COLLECTION_NAME,
        )
        return

    client.delete_permanently(collection_id, ids)
    log.info(
        "Permanently removed %d imported bookmark(s) from '%s'. "
        "Note: still-starred repos will be re-imported on the next sync.",
        len(ids),
        config.COLLECTION_NAME,
    )


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    parser = argparse.ArgumentParser(prog="raindrop_stars")
    subs = parser.add_subparsers(dest="command")

    cleanup_parser = subs.add_parser(
        "cleanup",
        help="Permanently delete the bookmarks this tool imported.",
    )
    cleanup_parser.add_argument(
        "--yes",
        action="store_true",
        help="Confirm permanent deletion (required).",
    )

    args = parser.parse_args()

    if args.command == "cleanup":
        cleanup(args.yes)
    else:
        sync()


if __name__ == "__main__":
    main()
