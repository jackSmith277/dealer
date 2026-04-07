
#!/usr/bin/env python3
"""
Scrape public post-purchase car reviews from pages on sites like Dongchedi
and Autohome.

Notes:
- This script is intended for public pages you are allowed to access.
- HTML structures on these sites change frequently, so selectors may need
  maintenance over time.
- Some pages require login, extra interaction, or stronger anti-bot measures;
  in those cases, this script will collect only the content it can access.

Examples:
  python car_review_scraper.py ^
    --url "https://www.dongchedi.com/auto/series/score/1234-x-x-x-x" ^
    --site dongchedi ^
    --max-items 50 ^
    --format csv ^
    --output dongchedi_reviews.csv

  python car_review_scraper.py ^
    --url "https://k.autohome.com.cn/1234/" ^
    --site autohome ^
    --format json ^
    --output autohome_reviews.json
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import time
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Tuple
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from openpyxl import Workbook
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright
# python 汽车服务/新爬取.py --url "https://www.dongchedi.com/auto/series/score/6187-x-x-x-x-x" --site dongchedi --max-items 20 --format json --output reviews.json --print-comments
# python car_review_scraper.py --url "https://www.dongchedi.com/auto/series/score/6187-x-x-x-x-x" --site dongchedi --output reviews.xlsx
# python 汽车服务/新爬取.py --url "https://www.dongchedi.com/auto/series/score/4499-x-x-x-x-x"  --url "https://www.dongchedi.com/auto/series/score/6187-x-x-x-x-x"   --site dongchedi --output  reviews.xlsx


def clean_text(value: Optional[str]) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip()


def first_text(node, selectors: Iterable[str]) -> str:
    for selector in selectors:
        found = node.select_one(selector)
        if found:
            text = clean_text(found.get_text(" ", strip=True))
            if text:
                return text
    return ""


def first_attr(node, selectors: Iterable[str], attr_name: str) -> str:
    for selector in selectors:
        found = node.select_one(selector)
        if found and found.has_attr(attr_name):
            value = clean_text(found.get(attr_name))
            if value:
                return value
    return ""


def maybe_rating(value: str) -> str:
    if not value:
        return ""
    match = re.search(r"(\d+(?:\.\d+)?)", value)
    return match.group(1) if match else value


def extract_date(value: str) -> str:
    if not value:
        return ""
    match = re.search(r"(\d{4}-\d{2}-\d{2})", value)
    if match:
        return match.group(1)
    match = re.search(r"(\d{4}-\d{2})", value)
    return match.group(1) if match else ""


def clean_review_content(value: str) -> str:
    if not value:
        return ""

    text = clean_text(value)
    text = re.sub(r"^优秀\s*[”\"]?\s*", "", text)
    text = re.sub(r"查看完整点评.*$", "", text)
    text = re.sub(r"\d{4}-\d{2}-\d{2}\s+\d+评论\s+\d+赞同\s+分享.*$", "", text)
    text = re.sub(r"\d{4}-\d{2}-\d{2}\s+\d+评论.*$", "", text)
    return clean_text(text)


def normalize_review(review: Dict[str, str]) -> Dict[str, str]:
    normalized = dict(review)
    normalized["published_at"] = extract_date(normalized.get("published_at", "")) or extract_date(
        normalized.get("content", "")
    )
    normalized["rating"] = maybe_rating(normalized.get("rating", ""))
    normalized["content"] = clean_review_content(normalized.get("content", ""))
    return normalized


def review_sort_key(review: Dict[str, str]) -> tuple[int, str]:
    published_at = review.get("published_at", "") or ""
    if published_at:
        return (1, published_at)
    return (0, "")


def excel_rows(rows: List[Dict[str, str]]) -> List[List[str]]:
    output = []
    for row in rows:
        cleaned = normalize_review(row)
        output.append(
            [
                cleaned.get("published_at", ""),
                cleaned.get("car_name", "") or cleaned.get("title", ""),
                cleaned.get("rating", ""),
                cleaned.get("content", ""),
            ]
        )
    return output


def safe_sheet_name(name: str, used_names: set[str]) -> str:
    candidate = re.sub(r'[\\/*?:\[\]]', "_", name).strip()
    candidate = candidate[:31] or "车型评论"
    base = candidate
    counter = 2
    while candidate in used_names:
        suffix = f"_{counter}"
        candidate = f"{base[:31 - len(suffix)]}{suffix}"
        counter += 1
    used_names.add(candidate)
    return candidate


def infer_sheet_name(url: str, rows: List[Dict[str, str]]) -> str:
    for row in rows:
        car_name = row.get("car_name", "") or row.get("title", "")
        if car_name:
            return car_name
    path = urlparse(url).path.rstrip("/").split("/")[-1]
    return path or "车型评论"


@dataclass
class SiteConfig:
    name: str
    domains: List[str]
    review_item_selectors: List[str]
    content_selectors: List[str]
    user_selectors: List[str] = field(default_factory=list)
    date_selectors: List[str] = field(default_factory=list)
    title_selectors: List[str] = field(default_factory=list)
    rating_selectors: List[str] = field(default_factory=list)
    car_selectors: List[str] = field(default_factory=list)
    city_selectors: List[str] = field(default_factory=list)
    next_page_selectors: List[str] = field(default_factory=list)


SITE_CONFIGS: Dict[str, SiteConfig] = {
    "dongchedi": SiteConfig(
        name="dongchedi",
        domains=["dongchedi.com"],
        review_item_selectors=[
            "[data-testid='ugc-comment-item']",
            ".tw-mb-16.tw-rounded-12",
            ".review-list-item",
            ".user-comment-item",
            ".list-item",
        ],
        content_selectors=[
            "[data-testid='ugc-content']",
            ".jsx-3490361950",
            ".comment-content",
            ".text",
            "p",
        ],
        user_selectors=[
            "[data-testid='user-name']",
            ".user-name",
            ".name",
            ".nickname",
        ],
        date_selectors=[
            "time",
            ".date",
            ".time",
            ".publish-time",
        ],
        title_selectors=[
            "h3",
            "h4",
            ".title",
            ".comment-title",
        ],
        rating_selectors=[
            "[data-testid='score']",
            ".score",
            ".rating",
            ".star-score",
        ],
        car_selectors=[
            ".series-name",
            ".car-name",
            ".vehicle-name",
        ],
        city_selectors=[
            ".city",
            ".location",
        ],
        next_page_selectors=[
            "a.next",
            "button.next",
            "li.ant-pagination-next button",
            "li.ant-pagination-next a",
        ],
    ),
    "autohome": SiteConfig(
        name="autohome",
        domains=["autohome.com.cn"],
        review_item_selectors=[
            ".mouthcon",
            ".choose-con",
            ".kb-con",
            ".mainPart",
            ".content",
        ],
        content_selectors=[
            ".text-con",
            ".koubei-final",
            ".kb-item-cont",
            ".content > p",
            "p",
        ],
        user_selectors=[
            ".name-text",
            ".user-name",
            ".koubei-owner",
            ".name",
        ],
        date_selectors=[
            ".date",
            ".time",
            ".kb-item-time",
        ],
        title_selectors=[
            ".title-name",
            ".koubei-title",
            "h3",
            "h4",
        ],
        rating_selectors=[
            ".font-arial",
            ".kb-item-score",
            ".score-number",
        ],
        car_selectors=[
            ".subnav-title-name",
            ".main-title",
            ".car-type",
        ],
        city_selectors=[
            ".from",
            ".city",
            ".place",
        ],
        next_page_selectors=[
            "a.next",
            ".pagination .next-page",
            ".page-item-next a",
        ],
    ),
}


def detect_site(url: str, explicit_site: Optional[str]) -> SiteConfig:
    if explicit_site:
        site = SITE_CONFIGS.get(explicit_site.lower())
        if not site:
            supported = ", ".join(sorted(SITE_CONFIGS))
            raise ValueError(f"Unsupported --site value: {explicit_site}. Supported: {supported}")
        return site

    hostname = urlparse(url).netloc.lower()
    for config in SITE_CONFIGS.values():
        if any(domain in hostname for domain in config.domains):
            return config
    supported = ", ".join(sorted(SITE_CONFIGS))
    raise ValueError(f"Could not detect site from URL: {url}. Please pass --site. Supported: {supported}")


def extract_reviews_from_html(html: str, source_url: str, site: SiteConfig) -> List[Dict[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    review_nodes = []
    for selector in site.review_item_selectors:
        review_nodes = soup.select(selector)
        if review_nodes:
            break

    reviews: List[Dict[str, str]] = []
    for node in review_nodes:
        content = first_text(node, site.content_selectors)
        user_name = first_text(node, site.user_selectors)
        published_at = first_text(node, site.date_selectors)
        title = first_text(node, site.title_selectors)
        rating = maybe_rating(first_text(node, site.rating_selectors))
        car_name = first_text(node, site.car_selectors)
        city = first_text(node, site.city_selectors)

        if not any([content, title, user_name]):
            continue

        reviews.append(
            {
                "site": site.name,
                "source_url": source_url,
                "car_name": car_name,
                "title": title,
                "content": content,
                "rating": rating,
                "user_name": user_name,
                "city": city,
                "published_at": published_at,
            }
        )

    if reviews:
        return reviews

    # Fallback: try JSON-LD when the visible DOM structure is unstable.
    script_nodes = soup.select("script[type='application/ld+json']")
    fallback_reviews: List[Dict[str, str]] = []
    for script in script_nodes:
        raw = clean_text(script.string or script.get_text())
        if not raw:
            continue
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            continue

        entries = payload if isinstance(payload, list) else [payload]
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            if entry.get("@type") not in {"Review", "UserComments"}:
                continue
            author = entry.get("author")
            if isinstance(author, dict):
                author_name = clean_text(author.get("name"))
            else:
                author_name = clean_text(str(author or ""))

            review_rating = entry.get("reviewRating", {})
            if isinstance(review_rating, dict):
                rating_value = clean_text(str(review_rating.get("ratingValue", "")))
            else:
                rating_value = clean_text(str(review_rating or ""))

            item = {
                "site": site.name,
                "source_url": source_url,
                "car_name": clean_text(str(entry.get("itemReviewed", ""))),
                "title": clean_text(str(entry.get("name", ""))),
                "content": clean_text(str(entry.get("reviewBody", ""))),
                "rating": maybe_rating(rating_value),
                "user_name": author_name,
                "city": "",
                "published_at": clean_text(str(entry.get("datePublished", ""))),
            }
            if any([item["content"], item["title"], item["user_name"]]):
                fallback_reviews.append(item)

    return fallback_reviews


def extract_article_links_from_user_home(html: str) -> List[str]:
    soup = BeautifulSoup(html, "html.parser")
    urls = []
    seen = set()
    for anchor in soup.select("a[href]"):
        href = anchor.get("href", "").strip()
        if not href:
            continue
        if href.startswith("//"):
            href = "https:" + href
        elif href.startswith("/"):
            href = "https://www.dongchedi.com" + href
        if "/ugc/article/" not in href:
            continue
        href = href.split("?", 1)[0]
        if href in seen:
            continue
        seen.add(href)
        urls.append(href)
    return urls


def extract_article_from_html(html: str, source_url: str) -> Dict[str, str]:
    soup = BeautifulSoup(html, "html.parser")
    title = ""
    content = ""
    published_at = ""
    user_name = ""
    car_name = ""

    title_node = soup.select_one("h1")
    if title_node:
        title = clean_text(title_node.get_text(" ", strip=True))

    for selector in [
        ".article-content p",
        ".post-content p",
        "[data-testid='article-content'] p",
        ".RichText p",
        "article p",
    ]:
        paragraphs = [clean_text(node.get_text(" ", strip=True)) for node in soup.select(selector)]
        paragraphs = [text for text in paragraphs if text]
        if paragraphs:
            content = "\n".join(paragraphs)
            break

    if not content:
        meta_desc = soup.select_one("meta[name='description']")
        if meta_desc and meta_desc.get("content"):
            content = clean_text(meta_desc["content"])

    for selector in ["time", ".publish-time", ".date", ".time"]:
        node = soup.select_one(selector)
        if node:
            published_at = clean_text(node.get_text(" ", strip=True))
            if published_at:
                break

    for selector in [".user-name", ".name", ".author-name", "[data-testid='user-name']"]:
        node = soup.select_one(selector)
        if node:
            user_name = clean_text(node.get_text(" ", strip=True))
            if user_name:
                break

    for selector in [".series-name", ".car-name", ".vehicle-name", ".tag"]:
        node = soup.select_one(selector)
        if node:
            car_name = clean_text(node.get_text(" ", strip=True))
            if car_name:
                break

    return {
        "site": "dongchedi_user_home",
        "source_url": source_url,
        "car_name": car_name,
        "title": title,
        "content": content,
        "rating": "",
        "user_name": user_name,
        "city": "",
        "published_at": published_at,
    }


def ancestor_with_review_text(node):
    current = node
    for _ in range(8):
        if current is None:
            break
        text = clean_text(current.get_text(" ", strip=True))
        if "点评车型:" in text and len(text) > 100:
            return current
        current = current.parent
    return None


def extract_dongchedi_score_reviews_from_html(html: str, source_url: str) -> List[Dict[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    anchors = soup.select('a[href*="/koubei/"]')
    seen = set()
    reviews: List[Dict[str, str]] = []

    for anchor in anchors:
        href = anchor.get("href", "").strip()
        if not href:
            continue
        href = href.split("#", 1)[0]
        if href.startswith("/"):
            href = "https://www.dongchedi.com" + href
        if href in seen:
            continue

        card = ancestor_with_review_text(anchor)
        if card is None:
            continue
        seen.add(href)

        text = clean_text(card.get_text(" ", strip=True))
        if "点评车型:" not in text:
            continue

        title_match = re.search(r"点评车型:\s*(.*?)\s+(\d+(?:\.\d+)?)\s*分", text)
        if title_match:
            title = title_match.group(1).strip()
            rating = title_match.group(2).strip()
        else:
            title = ""
            rating = ""

        user_match = re.search(r"([^\s]+)\s+.*?车主", text)
        user_name = user_match.group(1).strip() if user_match else ""

        car_match = re.search(r"购买车型\s*(.*?)\s*\d{4}-\d{2}\s*提车时间", text)
        car_name = car_match.group(1).strip() if car_match else title

        time_match = re.search(r"(\d{4}-\d{2})\s*提车时间", text)
        published_at = time_match.group(1).strip() if time_match else ""

        city_match = re.search(r"提车时间\s*[^\s]+\s+购买地点\s*([^\s]+)", text)
        city = city_match.group(1).strip() if city_match else ""

        content = ""
        content_match = re.search(r"点评车型:.*?\d+(?:\.\d+)?\s*分\s*[“\"]?.*?[”\"]?\s*(.*)", text)
        if content_match:
            content = content_match.group(1).strip()
        if len(content) > 2000:
            content = content[:2000] + "..."

        if not content:
            continue

        reviews.append(
            {
                "site": "dongchedi",
                "source_url": href or source_url,
                "car_name": car_name,
                "title": title,
                "content": content,
                "rating": rating,
                "user_name": user_name,
                "city": city,
                "published_at": published_at,
            }
        )

    return unique_reviews(reviews)


def fetch_html(url: str) -> str:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/123.0.0.0 Safari/537.36"
        )
    }
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return response.text


def scroll_page(page, rounds: int, pause_seconds: float) -> None:
    last_height = 0
    for _ in range(rounds):
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(pause_seconds)
        try:
            current_height = page.evaluate("document.body.scrollHeight")
        except Exception:
            break
        if current_height == last_height:
            break
        last_height = current_height


def click_next_page(page, site: SiteConfig) -> bool:
    for selector in site.next_page_selectors:
        button = page.query_selector(selector)
        if not button:
            continue
        try:
            disabled = button.get_attribute("disabled")
            classes = button.get_attribute("class") or ""
            if disabled is not None or "disabled" in classes:
                continue
            button.click(timeout=3000)
            page.wait_for_load_state("networkidle", timeout=10000)
            return True
        except Exception:
            continue
    return False


def unique_reviews(reviews: List[Dict[str, str]]) -> List[Dict[str, str]]:
    seen = set()
    deduped = []
    for review in reviews:
        key = (
            review.get("site", ""),
            review.get("source_url", ""),
            review.get("user_name", ""),
            review.get("title", ""),
            review.get("content", ""),
            review.get("published_at", ""),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(review)
    return deduped


def scrape_url(
    url: str,
    site: SiteConfig,
    max_items: int,
    max_pages: int,
    scroll_rounds: int,
    pause_seconds: float,
    headless: bool,
    browser_executable: Optional[str],
    browser_channel: Optional[str],
) -> List[Dict[str, str]]:
    if site.name == "dongchedi" and "/auto/series/score/" in url:
        html = fetch_html(url)
        reviews = extract_dongchedi_score_reviews_from_html(html, url)
        if reviews:
            return reviews[:max_items]

    collected: List[Dict[str, str]] = []

    with sync_playwright() as playwright:
        launch_options = {"headless": headless}
        if browser_executable:
            launch_options["executable_path"] = browser_executable
        elif browser_channel:
            launch_options["channel"] = browser_channel

        browser = playwright.chromium.launch(**launch_options)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/123.0.0.0 Safari/537.36"
            ),
            locale="zh-CN",
            viewport={"width": 1440, "height": 2200},
        )
        page = context.new_page()

        try:
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_load_state("networkidle", timeout=15000)
        except PlaywrightTimeoutError:
            pass

        if site.name == "dongchedi" and "/user/" in urlparse(url).path:
            scroll_page(page, rounds=scroll_rounds, pause_seconds=pause_seconds)
            article_links = extract_article_links_from_user_home(page.content())
            for article_url in article_links[:max_items]:
                detail_page = context.new_page()
                try:
                    detail_page.goto(article_url, wait_until="domcontentloaded", timeout=30000)
                    detail_page.wait_for_load_state("networkidle", timeout=15000)
                except PlaywrightTimeoutError:
                    pass

                article = extract_article_from_html(detail_page.content(), detail_page.url)
                detail_page.close()
                if any([article["title"], article["content"]]):
                    collected.append(article)
            browser.close()
            return unique_reviews(collected)[:max_items]

        for _ in range(max_pages):
            scroll_page(page, rounds=scroll_rounds, pause_seconds=pause_seconds)
            html = page.content()
            page_reviews = extract_reviews_from_html(html, page.url, site)
            collected.extend(page_reviews)
            collected = unique_reviews(collected)
            if len(collected) >= max_items:
                break
            if not click_next_page(page, site):
                break

        browser.close()

    return collected[:max_items]


def write_csv(output_path: str, rows: List[Dict[str, str]]) -> None:
    fieldnames = [
        "site",
        "source_url",
        "car_name",
        "title",
        "content",
        "rating",
        "user_name",
        "city",
        "published_at",
    ]
    with open(output_path, "w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(output_path: str, rows: List[Dict[str, str]]) -> None:
    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(rows, fh, ensure_ascii=False, indent=2)


def write_excel(output_path: str, sheet_data: List[Tuple[str, List[Dict[str, str]]]]) -> None:
    workbook = Workbook()
    default_sheet = workbook.active
    used_names: set[str] = set()

    for index, (url, rows) in enumerate(sheet_data):
        sheet = default_sheet if index == 0 else workbook.create_sheet()
        sheet.title = safe_sheet_name(infer_sheet_name(url, rows), used_names)
        sheet.append(["评论时间", "车型", "评分", "具体评论"])

        for row in excel_rows(rows):
            sheet.append(row)

        sheet.column_dimensions["A"].width = 14
        sheet.column_dimensions["B"].width = 36
        sheet.column_dimensions["C"].width = 10
        sheet.column_dimensions["D"].width = 120

    workbook.save(output_path)


def print_reviews(rows: List[Dict[str, str]]) -> None:
    if not rows:
        print("No reviews found.")
        return

    for index, row in enumerate(rows, start=1):
        print("-" * 60)
        print(f"[{index}] 用户: {row.get('user_name', '') or '未知'}")
        print(f"车型: {row.get('car_name', '') or '未知'}")
        print(f"标题: {row.get('title', '') or '无'}")
        print(f"评分: {row.get('rating', '') or '无'}")
        print(f"时间: {row.get('published_at', '') or '无'}")
        print(f"评论: {row.get('content', '') or '无'}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scrape public car owner reviews from supported websites.")
    parser.add_argument(
        "--url",
        action="append",
        required=True,
        help="Review list page URL. Repeat this argument to scrape multiple models.",
    )
    parser.add_argument("--site", help="Site key: dongchedi or autohome. If omitted, auto-detect from URL.")
    parser.add_argument("--output", default="reviews.xlsx", help="Output file path.")
    parser.add_argument("--format", choices=["json", "csv", "xlsx"], default="xlsx", help="Output format.")
    parser.add_argument("--max-items", type=int, default=100, help="Maximum number of reviews to keep per model URL.")
    parser.add_argument("--max-pages", type=int, default=5, help="Maximum number of pages to traverse.")
    parser.add_argument("--scroll-rounds", type=int, default=6, help="How many bottom-scroll rounds per page.")
    parser.add_argument("--pause-seconds", type=float, default=1.5, help="Wait time between page interactions.")
    parser.add_argument(
        "--headed",
        action="store_true",
        help="Run with browser UI visible. Useful when the site needs manual observation.",
    )
    parser.add_argument(
        "--browser-path",
        help="Use an existing local browser executable, for example Chrome or Edge.",
    )
    parser.add_argument(
        "--browser-channel",
        choices=["chrome", "msedge"],
        help="Launch a system-installed browser channel instead of Playwright-managed Chromium.",
    )
    parser.add_argument(
        "--print-comments",
        action="store_true",
        help="Print scraped comments to stdout.",
    )
    return parser.parse_args()


def detect_local_browser() -> tuple[Optional[str], Optional[str]]:
    candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    ]
    for path in candidates:
        if os.path.exists(path):
            return path, None
    return None, None


def main() -> None:
    args = parse_args()
    browser_path = args.browser_path
    browser_channel = args.browser_channel
    if not browser_path and not browser_channel:
        browser_path, browser_channel = detect_local_browser()

    all_reviews: List[Dict[str, str]] = []
    reviews_by_url: List[Tuple[str, List[Dict[str, str]]]] = []
    per_url_limit = max(1, args.max_items)

    for current_url in args.url:
        site = detect_site(current_url, args.site)
        reviews = scrape_url(
            url=current_url,
            site=site,
            max_items=per_url_limit,
            max_pages=args.max_pages,
            scroll_rounds=args.scroll_rounds,
            pause_seconds=args.pause_seconds,
            headless=not args.headed,
            browser_executable=browser_path,
            browser_channel=browser_channel,
        )
        reviews = [normalize_review(review) for review in reviews]
        reviews.sort(key=review_sort_key, reverse=True)
        reviews_by_url.append((current_url, reviews))
        all_reviews.extend(reviews)
        print(f"site={site.name}")
        print(f"url={current_url}")
        print(f"reviews={len(reviews)}")

    all_reviews.sort(key=review_sort_key, reverse=True)

    if args.format == "csv":
        write_csv(args.output, all_reviews)
    elif args.format == "xlsx":
        write_excel(args.output, reviews_by_url)
    else:
        write_json(args.output, all_reviews)

    print(f"output={args.output}")
    if args.print_comments:
        print_reviews(all_reviews)

    if not all_reviews:
        raise SystemExit(
            "No comments were scraped. Please confirm each URL is a public review list page and update the selectors if the site changed."
        )


if __name__ == "__main__":
    main()


class Solution(object):
    def plusOne(self, digits):
        sum = digits[len(digits) - 1] + 1
        digits[len(digits) - 1] = sum % 10
        carry = sum // 10
        for index in range(len(digits) - 2, -1, -1):
            sum = digits[index] + carry
            digits[index] = sum % 10
            carry = sum // 10
        if carry == 1:
            digits.append(0)
            for i in range(len(digits) - 1, 0, -1):
                digits[i + 1] = digits[i]
            digits[0] = 1
        return digits


digits = [9]
s = Solution()
print(s.plusOne(digits))