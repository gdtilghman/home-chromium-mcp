#!/usr/bin/env python3
"""Export storage state from Chromium's default browser context.

Run this script inside the Scrapling/home-browser container. It connects to
the visible Chromium instance over loopback CDP, exports the default
context's Playwright storage state, and writes it directly to the mounted
/data volume.

The script reports counts and page hosts only. It does not print cookie
names, cookie values, local-storage values, or complete page URLs.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export the GUI Chromium default context's storage state."
    )
    parser.add_argument(
        "--cdp-url",
        default="http://127.0.0.1:9222",
        help="CDP endpoint inside the shared network namespace.",
    )
    parser.add_argument(
        "--output",
        default="/data/browser-state.json",
        help="State file to write inside the container.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as playwright:
        browser = playwright.chromium.connect_over_cdp(args.cdp_url)

        if not browser.contexts:
            raise RuntimeError("Chromium did not expose a default browser context")

        context = browser.contexts[0]

        page_hosts = []
        for page in context.pages:
            parsed = urlparse(page.url)
            page_hosts.append(parsed.netloc or parsed.scheme or "unknown")

        state = context.storage_state(path=str(output))

        print(f"contexts: {len(browser.contexts)}")
        print(f"pages: {len(context.pages)}")
        for host in page_hosts:
            print(f"page host: {host}")
        print(f"cookies exported: {len(state.get('cookies', []))}")
        print(f"origins exported: {len(state.get('origins', []))}")
        print(f"state saved: {output}")

        # Closing a Playwright CDP connection disconnects this client;
        # it does not intentionally close the visible Chromium process.
        browser.close()


if __name__ == "__main__":
    main()
