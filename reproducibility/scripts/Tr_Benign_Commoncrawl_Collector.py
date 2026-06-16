#!/usr/bin/env python3
"""
collect_benign_tr_urls.py
=========================
Benign Turkish (.tr) URL collector for the TurkQuish corpus (TUMC).

This script harvests benign Turkish-domain URLs from the Common Crawl URL
index (CDX/CDXJ) and writes them to a CSV file. It is released to support
reproducibility of the benign-URL collection stage described in:

    F. Mussa and O. Oksuz, "TurkQuish: Explainable URL-Only Detection of
    QR-Code Phishing in the Turkish Web Ecosystem," Cluster Computing
    (under review).

The collector queries the per-crawl CDX endpoints listed at
https://index.commoncrawl.org/collinfo.json, restricting results to
successfully fetched HTML pages (HTTP 200, text/html) under the ``.tr``
country-code top-level domain. Only the decoded URL string and its parsed
components are retained; no page content is downloaded.

Design notes
------------
* Resilient transport: transient HTTP responses (429, 500, 502, 503, 504)
  and timeouts are retried with exponential backoff and jitter; 404 marks
  the end of an index rather than an error.
* Page discovery: the number of index pages is queried first
  (``showNumPages``) so empty crawls are skipped quickly.
* Parallelism: index pages within a crawl are fetched concurrently.
* Resumable: a JSON checkpoint records completed crawls and the running
  count, so an interrupted run resumes without re-fetching, and the
  in-memory de-duplication set is rebuilt from the existing CSV.
* Incremental output: rows are flushed per batch, so a partial run is
  still usable.

Coverage
--------
The Common Crawl CDX index server provides per-crawl indices from
``CC-MAIN-2013-20`` (May 2013) onward; crawls before 2013 use an older
archive format that is not exposed through this endpoint. Two early 2015
indices (``CC-MAIN-2015-06`` and ``CC-MAIN-2015-11``) lack the ``status``
and ``mime`` fields and therefore return no rows under the status/MIME
filter used here. These crawls are listed in ``DEFAULT_CRAWL_IDS`` for
completeness but are expected to yield no records; the effective coverage
of this configuration is 113 monthly indices spanning 2013-2025.

References
----------
* Common Crawl URL index: https://commoncrawl.org/cdxj-index
* CDX Server API (pagination): https://github.com/webrecorder/pywb/wiki/CDX-Server-API

License: MIT. Cite the manuscript above if you use this script.
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import random
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Iterable, Optional
from urllib.parse import urlparse

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

LOGGER = logging.getLogger("cc_tr_collector")

CDX_ENDPOINT = "https://index.commoncrawl.org/{crawl_id}-index"

# Per-crawl CDX indices, newest first. Crawls before CC-MAIN-2013-20 are not
# available through the CDX endpoint; CC-MAIN-2015-06 and CC-MAIN-2015-11 lack
# the status/mime fields and return no rows under the filter used here.
DEFAULT_CRAWL_IDS: tuple[str, ...] = (
    "CC-MAIN-2025-43", "CC-MAIN-2025-38", "CC-MAIN-2025-33", "CC-MAIN-2025-30",
    "CC-MAIN-2025-26", "CC-MAIN-2025-21", "CC-MAIN-2025-18", "CC-MAIN-2025-13",
    "CC-MAIN-2025-08", "CC-MAIN-2025-05",
    "CC-MAIN-2024-51", "CC-MAIN-2024-46", "CC-MAIN-2024-42", "CC-MAIN-2024-38",
    "CC-MAIN-2024-33", "CC-MAIN-2024-30", "CC-MAIN-2024-26", "CC-MAIN-2024-22",
    "CC-MAIN-2024-18", "CC-MAIN-2024-10",
    "CC-MAIN-2023-50", "CC-MAIN-2023-40", "CC-MAIN-2023-23", "CC-MAIN-2023-14",
    "CC-MAIN-2023-06",
    "CC-MAIN-2022-49", "CC-MAIN-2022-40", "CC-MAIN-2022-33", "CC-MAIN-2022-27",
    "CC-MAIN-2022-21", "CC-MAIN-2022-05",
    "CC-MAIN-2021-49", "CC-MAIN-2021-43", "CC-MAIN-2021-39", "CC-MAIN-2021-25",
    "CC-MAIN-2021-21", "CC-MAIN-2021-17", "CC-MAIN-2021-10", "CC-MAIN-2021-04",
    "CC-MAIN-2020-50", "CC-MAIN-2020-45", "CC-MAIN-2020-40", "CC-MAIN-2020-34",
    "CC-MAIN-2020-29", "CC-MAIN-2020-24", "CC-MAIN-2020-16", "CC-MAIN-2020-10",
    "CC-MAIN-2020-05",
    "CC-MAIN-2019-51", "CC-MAIN-2019-47", "CC-MAIN-2019-43", "CC-MAIN-2019-39",
    "CC-MAIN-2019-35", "CC-MAIN-2019-30", "CC-MAIN-2019-26", "CC-MAIN-2019-22",
    "CC-MAIN-2019-18", "CC-MAIN-2019-13", "CC-MAIN-2019-09", "CC-MAIN-2019-04",
    "CC-MAIN-2018-51", "CC-MAIN-2018-47", "CC-MAIN-2018-43", "CC-MAIN-2018-39",
    "CC-MAIN-2018-34", "CC-MAIN-2018-30", "CC-MAIN-2018-26", "CC-MAIN-2018-22",
    "CC-MAIN-2018-17", "CC-MAIN-2018-13", "CC-MAIN-2018-09", "CC-MAIN-2018-05",
    "CC-MAIN-2017-51", "CC-MAIN-2017-47", "CC-MAIN-2017-43", "CC-MAIN-2017-39",
    "CC-MAIN-2017-34", "CC-MAIN-2017-30", "CC-MAIN-2017-26", "CC-MAIN-2017-22",
    "CC-MAIN-2017-17", "CC-MAIN-2017-13", "CC-MAIN-2017-09", "CC-MAIN-2017-04",
    "CC-MAIN-2016-50", "CC-MAIN-2016-44", "CC-MAIN-2016-40", "CC-MAIN-2016-36",
    "CC-MAIN-2016-30", "CC-MAIN-2016-26", "CC-MAIN-2016-22", "CC-MAIN-2016-18",
    "CC-MAIN-2016-07",
    "CC-MAIN-2015-48", "CC-MAIN-2015-40", "CC-MAIN-2015-35", "CC-MAIN-2015-32",
    "CC-MAIN-2015-27", "CC-MAIN-2015-22", "CC-MAIN-2015-18", "CC-MAIN-2015-14",
    "CC-MAIN-2015-11", "CC-MAIN-2015-06",
    "CC-MAIN-2014-52", "CC-MAIN-2014-49", "CC-MAIN-2014-42", "CC-MAIN-2014-41",
    "CC-MAIN-2014-35", "CC-MAIN-2014-23", "CC-MAIN-2014-15", "CC-MAIN-2014-10",
    "CC-MAIN-2013-48", "CC-MAIN-2013-20",
)

# Static assets and binaries that are not useful as benign navigational URLs.
_BAD_EXTENSION = re.compile(
    r"\.(?:jpg|jpeg|png|gif|webp|svg|ico|pdf|zip|rar|gz|tar|"
    r"mp4|mp3|avi|mov|css|js|woff|woff2|ttf|exe|msi|apk|"
    r"xml|json|rss|bmp|tiff)(?:\?|$)",
    re.IGNORECASE,
)

CSV_FIELDS = ("url", "domain", "path", "subpath", "query", "label", "source", "crawl")


@dataclass
class CollectorConfig:
    """Runtime configuration for a collection run."""

    output_file: str
    crawl_ids: tuple[str, ...] = DEFAULT_CRAWL_IDS
    url_pattern: str = "*.tr/*"
    workers: int = 10
    max_retries: int = 6
    backoff_base: float = 2.0
    connect_timeout: float = 10.0
    read_timeout: float = 30.0
    query_limit: Optional[int] = None  # optional cap on rows per query (None = all)
    user_agent: str = (
        "TurkQuish-CC-Collector/1.0 (+research; reproducibility) "
        "python-requests"
    )

    @property
    def checkpoint_file(self) -> str:
        return self.output_file.replace(".csv", "") + "_checkpoint.json"

    @property
    def timeout(self) -> tuple[float, float]:
        return (self.connect_timeout, self.read_timeout)


@dataclass
class RunState:
    """Mutable, thread-shared state for a run."""

    seen_urls: set = field(default_factory=set)
    seen_lock: threading.Lock = field(default_factory=threading.Lock)
    write_lock: threading.Lock = field(default_factory=threading.Lock)


def build_session(cfg: CollectorConfig) -> requests.Session:
    """Create a configured ``requests`` session."""
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": cfg.user_agent,
            "Accept": "application/json, text/plain, */*",
            "Connection": "close",
        }
    )
    return session


# --------------------------------------------------------------------------- #
# Checkpointing
# --------------------------------------------------------------------------- #
def load_checkpoint(cfg: CollectorConfig) -> dict:
    """Load the checkpoint file, or return an empty state."""
    if os.path.exists(cfg.checkpoint_file):
        with open(cfg.checkpoint_file, encoding="utf-8") as handle:
            checkpoint = json.load(handle)
        LOGGER.info(
            "Checkpoint found: %d crawls done, %s URLs saved",
            len(checkpoint.get("done_crawls", [])),
            f"{checkpoint.get('total_saved', 0):,}",
        )
        return checkpoint
    return {"done_crawls": [], "total_saved": 0}


def save_checkpoint(cfg: CollectorConfig, done_crawls: Iterable[str], total_saved: int) -> None:
    """Persist progress so an interrupted run can resume."""
    tmp_path = cfg.checkpoint_file + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as handle:
        json.dump({"done_crawls": sorted(done_crawls), "total_saved": total_saved}, handle)
    os.replace(tmp_path, cfg.checkpoint_file)  # atomic on POSIX and Windows


def rebuild_seen_urls(cfg: CollectorConfig) -> set:
    """Rebuild the de-duplication set from an existing output CSV."""
    seen: set = set()
    if not os.path.exists(cfg.output_file):
        return seen
    LOGGER.info("Rebuilding de-duplication set from existing CSV ...")
    with open(cfg.output_file, encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader, None)
        url_idx = header.index("url") if header and "url" in header else 0
        for row in reader:
            if row:
                seen.add(row[url_idx])
    LOGGER.info("Loaded %s existing URLs", f"{len(seen):,}")
    return seen


# --------------------------------------------------------------------------- #
# Index queries
# --------------------------------------------------------------------------- #
def get_num_pages(session: requests.Session, cfg: CollectorConfig, index_url: str) -> Optional[int]:
    """Return the number of index pages for the query, or None on failure.

    A return value of 0 means the index exists but has no matching rows;
    None means the index could not be reached after retries.
    """
    params = {
        "url": cfg.url_pattern,
        "output": "json",
        "filter": ["status:200"],
        "mime": "text/html",
        "showNumPages": "true",
    }
    for attempt in range(4):
        try:
            response = session.get(index_url, params=params, timeout=cfg.timeout, verify=False)
            if response.status_code == 404:
                return 0
            response.raise_for_status()
            text = response.text.strip()
            if text.isdigit():
                return int(text)
            try:
                data = json.loads(text)
                if isinstance(data, dict):
                    return int(data.get("pages", data.get("pageCount", 1)))
                if isinstance(data, list) and data:
                    return int(data[0].get("pages", 1))
            except (ValueError, TypeError, KeyError):
                pass
            return 1
        except requests.RequestException as exc:
            wait = cfg.backoff_base ** attempt + random.uniform(0, 1)
            LOGGER.debug("num_pages retry %d: %s (sleep %.1fs)", attempt + 1, exc, wait)
            time.sleep(wait)
    return None


def fetch_page(session: requests.Session, cfg: CollectorConfig, index_url: str, page: int) -> Optional[list]:
    """Fetch one index page and return parsed JSON records.

    Returns an empty list for a 404 (end of index) and None if the page
    could not be retrieved after ``max_retries`` attempts.
    """
    params = {
        "url": cfg.url_pattern,
        "output": "json",
        "page": page,
        "filter": ["status:200"],
        "mime": "text/html",
    }
    if cfg.query_limit:
        params["limit"] = cfg.query_limit

    for attempt in range(cfg.max_retries):
        try:
            response = session.get(
                index_url, params=params, stream=True, timeout=cfg.timeout, verify=False
            )
            if response.status_code == 404:
                return []
            if response.status_code in (429, 500, 502, 503, 504):
                wait = cfg.backoff_base ** attempt + random.uniform(0, 2)
                LOGGER.warning(
                    "page %d HTTP %d, retry %d/%d in %.1fs",
                    page, response.status_code, attempt + 1, cfg.max_retries, wait,
                )
                time.sleep(wait)
                continue
            response.raise_for_status()
            records = []
            for line in response.iter_lines():
                if not line:
                    continue
                try:
                    records.append(json.loads(line.decode("utf-8")))
                except (ValueError, UnicodeDecodeError):
                    continue
            return records
        except requests.exceptions.Timeout:
            wait = cfg.backoff_base ** attempt + random.uniform(0, 2)
            LOGGER.warning("page %d timeout, retry %d/%d in %.1fs",
                           page, attempt + 1, cfg.max_retries, wait)
            time.sleep(wait)
        except requests.exceptions.RequestException as exc:
            wait = cfg.backoff_base ** attempt + random.uniform(0, 1)
            LOGGER.warning("page %d %s, retry %d/%d in %.1fs",
                           page, type(exc).__name__, attempt + 1, cfg.max_retries, wait)
            time.sleep(wait)

    LOGGER.error("page %d gave up after %d attempts", page, cfg.max_retries)
    return None


def parse_record(record: dict, crawl_id: str) -> Optional[dict]:
    """Validate and normalise a single CDX record into an output row."""
    url = record.get("url", "")
    if not url or _BAD_EXTENSION.search(url):
        return None
    try:
        parsed = urlparse(url)
    except ValueError:
        return None
    host = (parsed.hostname or "").lower()
    if not host.endswith(".tr") and ".tr/" not in (host + "/"):
        # Require a .tr host; endswith handles the common case, the second
        # clause is a defensive fallback for odd host strings.
        if not host.endswith(".tr"):
            return None
    path = parsed.path or "/"
    return {
        "url": url,
        "domain": host,
        "path": path,
        "subpath": path.lstrip("/"),
        "query": (parsed.query or "")[:300],
        "label": "benign",
        "source": "commoncrawl",
        "crawl": crawl_id,
    }


# --------------------------------------------------------------------------- #
# Per-crawl processing
# --------------------------------------------------------------------------- #
def process_crawl(cfg: CollectorConfig, state: RunState, writer: "csv._writer", crawl_id: str) -> int:
    """Collect benign .tr URLs from a single crawl. Returns rows written."""
    index_url = CDX_ENDPOINT.format(crawl_id=crawl_id)
    session = build_session(cfg)
    LOGGER.info("Processing %s (pattern %s)", crawl_id, cfg.url_pattern)

    num_pages = get_num_pages(session, cfg, index_url)
    if num_pages is None:
        LOGGER.warning("%s: page count unavailable, skipping", crawl_id)
        return 0
    if num_pages == 0:
        LOGGER.info("%s: no matching pages", crawl_id)
        return 0
    LOGGER.info("%s: %d page(s)", crawl_id, num_pages)

    written = 0
    with ThreadPoolExecutor(max_workers=cfg.workers) as executor:
        for start in range(0, num_pages, cfg.workers):
            batch = range(start, min(start + cfg.workers, num_pages))
            futures = {
                executor.submit(fetch_page, session, cfg, index_url, page): page
                for page in batch
            }
            for future in as_completed(futures):
                page = futures[future]
                try:
                    records = future.result()
                except Exception as exc:  # noqa: BLE001 - log and continue
                    LOGGER.error("%s page %d failed: %s", crawl_id, page, exc)
                    continue
                if not records:
                    continue

                rows = []
                for record in records:
                    parsed = parse_record(record, crawl_id)
                    if parsed is None:
                        continue
                    with state.seen_lock:
                        if parsed["url"] in state.seen_urls:
                            continue
                        state.seen_urls.add(parsed["url"])
                    rows.append(parsed)

                if rows:
                    with state.write_lock:
                        for row in rows:
                            writer.writerow([row[field] for field in CSV_FIELDS])
                    written += len(rows)
                    if written % 1000 < len(rows):
                        LOGGER.info("%s: %s rows so far", crawl_id, f"{written:,}")

    LOGGER.info("Done %s -> %s rows", crawl_id, f"{written:,}")
    return written


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def run(cfg: CollectorConfig) -> int:
    """Execute a full collection run. Returns total rows written."""
    os.makedirs(os.path.dirname(os.path.abspath(cfg.output_file)) or ".", exist_ok=True)

    checkpoint = load_checkpoint(cfg)
    done_crawls = set(checkpoint.get("done_crawls", []))
    total_saved = checkpoint.get("total_saved", 0)

    resuming = os.path.exists(cfg.output_file) and total_saved > 0
    state = RunState(seen_urls=rebuild_seen_urls(cfg) if resuming else set())
    file_mode = "a" if resuming else "w"

    remaining = [c for c in cfg.crawl_ids if c not in done_crawls]
    LOGGER.info("Output : %s", cfg.output_file)
    LOGGER.info("Mode   : %s", "RESUME" if resuming else "FRESH")
    LOGGER.info("Crawls : %d of %d remaining", len(remaining), len(cfg.crawl_ids))
    LOGGER.info("Saved  : %s", f"{total_saved:,}")

    with open(cfg.output_file, file_mode, newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        if file_mode == "w":
            writer.writerow(CSV_FIELDS)

        for crawl_id in cfg.crawl_ids:
            if crawl_id in done_crawls:
                LOGGER.info("Skip (done): %s", crawl_id)
                continue
            try:
                written = process_crawl(cfg, state, writer, crawl_id)
                handle.flush()
                total_saved += written
                done_crawls.add(crawl_id)
                save_checkpoint(cfg, done_crawls, total_saved)
                LOGGER.info("Running total: %s", f"{total_saved:,}")
            except KeyboardInterrupt:
                LOGGER.warning("Interrupted; checkpoint saved")
                save_checkpoint(cfg, done_crawls, total_saved)
                break
            except Exception as exc:  # noqa: BLE001 - record and continue
                LOGGER.error("Crawl %s error: %s; continuing", crawl_id, exc)
                save_checkpoint(cfg, done_crawls, total_saved)

    LOGGER.info("Complete: %s unique URLs -> %s", f"{total_saved:,}", cfg.output_file)
    return total_saved


def parse_args(argv: Optional[list] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Collect benign Turkish (.tr) URLs from the Common Crawl URL index.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("-o", "--output", default="benign_tr_urls.csv",
                        help="Output CSV path")
    parser.add_argument("--pattern", default="*.tr/*",
                        help="CDX URL match pattern")
    parser.add_argument("--workers", type=int, default=10,
                        help="Concurrent index-page fetches per crawl")
    parser.add_argument("--max-retries", type=int, default=6,
                        help="Retries per page on transient errors")
    parser.add_argument("--limit", type=int, default=None,
                        help="Optional cap on rows per index query")
    parser.add_argument("--crawls", nargs="+", default=None,
                        help="Explicit crawl IDs (default: built-in 2013-2025 list)")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Enable debug logging")
    return parser.parse_args(argv)


def main(argv: Optional[list] = None) -> int:
    args = parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s  %(levelname)-7s  %(message)s",
        datefmt="%H:%M:%S",
    )
    cfg = CollectorConfig(
        output_file=args.output,
        crawl_ids=tuple(args.crawls) if args.crawls else DEFAULT_CRAWL_IDS,
        url_pattern=args.pattern,
        workers=args.workers,
        max_retries=args.max_retries,
        query_limit=args.limit,
    )
    run(cfg)
    return 0


if __name__ == "__main__":
    sys.exit(main())