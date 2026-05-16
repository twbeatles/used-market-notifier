"""Optional live smoke check for marketplace search page structure.

This script is intentionally not part of the default unittest suite because it
depends on live websites and may be affected by rate limits or layout changes.
"""

from __future__ import annotations

import argparse
import asyncio
import json
from datetime import datetime
from pathlib import Path
import sys
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from playwright.async_api import async_playwright

from scrapers.marketplace_parsers import (
    evaluate_scrape_quality,
    parse_bunjang_search_items,
    parse_html_snapshot,
    parse_joonggonara_search_items,
)
from scrapers.playwright_danggeun import PlaywrightDanggeunScraper


def _urls(keyword: str) -> dict[str, str]:
    encoded = quote(keyword)
    return {
        "danggeun": f"https://www.daangn.com/kr/buy-sell/?search={encoded}&sort=recent",
        "bunjang": f"https://m.bunjang.co.kr/search/products?q={encoded}&order=date",
        "joonggonara": (
            "https://search.naver.com/search.naver"
            f"?where=article&ssc=tab.cafe.all&query={encoded}%20site%3Acafe.naver.com%2Fjoonggonara"
        ),
    }


async def _inspect_platform(page, platform: str, url: str, keyword: str, save_artifacts: bool) -> dict[str, object]:
    response = await page.goto(url, wait_until="domcontentloaded", timeout=25_000)
    await page.wait_for_timeout(2500)
    html = await page.content()
    snapshot = parse_html_snapshot(html)

    if platform == "danggeun":
        scraper = object.__new__(PlaywrightDanggeunScraper)
        items, metrics = scraper._parse_snapshot_items(snapshot, keyword)
        candidate_count = metrics.get("json_ld_item_count", 0) or metrics.get("dom_card_count", 0)
    elif platform == "bunjang":
        items, metrics = parse_bunjang_search_items(snapshot, keyword)
        candidate_count = metrics.get("dom_product_link_count", 0) or metrics.get("dom_card_count", 0)
    else:
        items = parse_joonggonara_search_items(html, keyword)
        metrics = {
            "cafe_link_count": await page.locator("a[href*='cafe.naver.com/joonggonara/']").count(),
        }
        candidate_count = metrics["cafe_link_count"]

    quality = evaluate_scrape_quality(platform, items)
    ok = bool((response is None or response.status < 400) and candidate_count and items and not quality["malformed"])
    result = {
        "platform": platform,
        "status": response.status if response else None,
        "url": url,
        "candidate_count": candidate_count,
        "item_count": len(items),
        "quality": quality,
        "sample": [
            {"id": item.article_id, "title": item.title, "price": item.price, "link": item.link}
            for item in items[:3]
        ],
        "ok": ok,
    }

    if not ok and save_artifacts:
        out_dir = ROOT / "debug_output"
        out_dir.mkdir(exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_keyword = "".join(ch if ch.isalnum() else "_" for ch in keyword)[:30]
        base = out_dir / f"live_smoke_{platform}_{safe_keyword}_{stamp}"
        (base.with_suffix(".html")).write_text(html, encoding="utf-8")
        (base.with_suffix(".json")).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        await page.screenshot(path=str(base.with_suffix(".png")), full_page=True)
        result["artifact_base"] = str(base)

    return result


async def _main() -> int:
    parser = argparse.ArgumentParser(description="Run optional live smoke checks for marketplace scrapers.")
    parser.add_argument("--keyword", default="아이폰")
    parser.add_argument("--platform", choices=["all", "danggeun", "bunjang", "joonggonara"], default="all")
    parser.add_argument("--no-artifacts", action="store_true", help="Do not write debug_output artifacts on failure.")
    args = parser.parse_args()

    urls = _urls(args.keyword)
    targets = list(urls) if args.platform == "all" else [args.platform]

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context(locale="ko-KR", timezone_id="Asia/Seoul")
        page = await context.new_page()
        results = []
        for platform in targets:
            results.append(
                await _inspect_platform(page, platform, urls[platform], args.keyword, not args.no_artifacts)
            )
        await browser.close()

    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0 if all(result["ok"] for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_main()))
