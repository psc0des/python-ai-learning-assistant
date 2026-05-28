"""Download Inter and JetBrains Mono from Google Fonts for offline use.

Run once from the repo root:
    python scripts/vendor_fonts.py

Output:
    static/vendor/fonts/          ← woff2 files
    static/vendor/fonts.css       ← @font-face declarations using local paths
"""

from __future__ import annotations

import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent.parent
FONTS_DIR = ROOT / "static" / "vendor" / "fonts"
FONTS_CSS = ROOT / "static" / "vendor" / "fonts.css"

FONTS_DIR.mkdir(parents=True, exist_ok=True)

GOOGLE_FONTS_URLS = [
    "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap",
    "https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&display=swap",
]

WOFF2_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


def _fetch(url: str, headers: dict | None = None) -> bytes:
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def vendor_fonts() -> None:
    combined_css_parts: list[str] = []

    for fonts_url in GOOGLE_FONTS_URLS:
        print(f"[fonts] Fetching CSS: {fonts_url}")
        css_bytes = _fetch(fonts_url, {"User-Agent": WOFF2_UA})
        css_text = css_bytes.decode("utf-8")

        woff2_urls = re.findall(r"url\((https://[^)]+\.woff2)\)", css_text)
        print(f"        Found {len(woff2_urls)} woff2 file(s)")

        for woff2_url in woff2_urls:
            filename = woff2_url.split("/")[-1].split("?")[0]
            local_path = FONTS_DIR / filename
            if not local_path.exists():
                print(f"        Downloading {filename}")
                data = _fetch(woff2_url)
                local_path.write_bytes(data)
            else:
                print(f"        Already exists: {filename}")
            css_text = css_text.replace(woff2_url, f"/vendor/fonts/{filename}")

        combined_css_parts.append(css_text)

    FONTS_CSS.write_text("\n".join(combined_css_parts), encoding="utf-8")
    print(f"[fonts] Written: {FONTS_CSS}")


if __name__ == "__main__":
    vendor_fonts()
