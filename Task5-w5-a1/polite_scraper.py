"""
Polite Web Scraper Pipeline (Task5-w5-a1)
Tracks: Backend AI Engineering (Week 5)

Pipeline Flow:
1. FETCH (Robots.txt check + Polite User-Agent + Rate Limit Delays + Exponential Backoff)
2. PARSE (HTML Parsing via BeautifulSoup4)
3. EXTRACT (Field Extraction: Title, Price, Rating, Availability, Category, Description)
4. CLEAN (Sanitize text, convert currency to float, convert rating words to int)
5. STRUCTURE (Pydantic Validation -> Export as corpus.jsonl for Week 6 RAG Corpus)
"""

import os
import re
import sys
import time
import json
import logging
import argparse
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import httpx
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field, HttpUrl, field_validator

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("PoliteScraper")

# Default User-Agent identifying the bot politely
DEFAULT_USER_AGENT = "FlyRank-PoliteScraper/1.0 (+https://github.com/Rytnix786/first-api-endpoint; contact@flyrank.ai)"
RATING_MAP = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5}


class ScrapedProduct(BaseModel):
    """Pydantic Schema for Structured Scraped Records (RAG Corpus ready)"""
    title: str = Field(..., description="Cleaned product title")
    price_gbp: float = Field(..., description="Price in GBP as float")
    rating_stars: int = Field(..., ge=1, le=5, description="Star rating 1-5")
    availability: str = Field(..., description="Stock availability status")
    category: str = Field(..., description="Product category name")
    product_description: Optional[str] = Field(None, description="Cleaned product description text")
    url: str = Field(..., description="Source page URL")
    scraped_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @field_validator('title', 'category')
    def strip_whitespace(cls, v: str) -> str:
        return v.strip()


class RobotsChecker:
    """Class responsible for parsing and enforcing robots.txt rules"""

    def __init__(self, user_agent: str = DEFAULT_USER_AGENT):
        self.user_agent = user_agent
        self.parsers: Dict[str, RobotFileParser] = {}

    def is_allowed(self, url: str) -> bool:
        """Check if URL is allowed under the site's robots.txt policy"""
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        robots_url = urljoin(base_url, "/robots.txt")

        if base_url not in self.parsers:
            rp = RobotFileParser()
            rp.set_url(robots_url)
            try:
                logger.info(f"Checking robots.txt at: {robots_url}")
                response = httpx.get(robots_url, headers={"User-Agent": self.user_agent}, timeout=5.0)
                if response.status_code == 200:
                    rp.parse(response.text.splitlines())
                else:
                    logger.warning(f"robots.txt returned status {response.status_code}, defaulting to allow.")
                    rp.allow_all = True
            except Exception as e:
                logger.warning(f"Could not fetch robots.txt ({e}), defaulting to allow.")
                rp.allow_all = True
            self.parsers[base_url] = rp

        return self.parsers[base_url].can_fetch(self.user_agent, url)


class PoliteFetcher:
    """HTTP Client with politeness controls: User-Agent, Rate Limit Delays, and Retries"""

    def __init__(
        self,
        user_agent: str = DEFAULT_USER_AGENT,
        delay_seconds: float = 1.0,
        max_retries: int = 3,
        timeout_seconds: float = 10.0
    ):
        self.user_agent = user_agent
        self.delay_seconds = delay_seconds
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds
        self.robots_checker = RobotsChecker(user_agent=self.user_agent)
        self.last_request_time: float = 0.0
        self.client = httpx.Client(
            headers={"User-Agent": self.user_agent, "Accept": "text/html,application/xhtml+xml"},
            timeout=self.timeout_seconds,
            follow_redirects=True
        )

    def fetch(self, url: str) -> Optional[str]:
        """Fetch page content while adhering to robots.txt, rate limits, and retries"""
        if not self.robots_checker.is_allowed(url):
            logger.error(f"[DENIED] Access denied by robots.txt for URL: {url}")
            return None

        # Enforce Rate Limiting (Politeness Sleep)
        elapsed = time.time() - self.last_request_time
        if elapsed < self.delay_seconds:
            sleep_time = self.delay_seconds - elapsed
            logger.debug(f"[WAIT] Politeness delay: sleeping for {sleep_time:.2f}s...")
            time.sleep(sleep_time)

        # Execute HTTP Request with Exponential Backoff
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"Fetching [Attempt {attempt}/{self.max_retries}]: {url}")
                response = self.client.get(url)
                self.last_request_time = time.time()

                if response.status_code == 200:
                    return response.text
                elif response.status_code in (429, 500, 502, 503, 504):
                    backoff = 2 ** attempt
                    logger.warning(f"HTTP {response.status_code} received. Retrying in {backoff}s...")
                    time.sleep(backoff)
                else:
                    logger.error(f"HTTP {response.status_code} client error for URL: {url}")
                    return None
            except Exception as e:
                logger.warning(f"Request exception on attempt {attempt}: {e}")
                if attempt == self.max_retries:
                    logger.error(f"Failed to fetch {url} after {self.max_retries} attempts.")
                    return None
                time.sleep(2 ** attempt)

        return None


class DataExtractorCleaner:
    """Parses HTML, extracts raw fields, and cleans data into valid typed fields"""

    @staticmethod
    def parse_product_page(html_content: str, url: str) -> Optional[ScrapedProduct]:
        """Parse single product detail page"""
        soup = BeautifulSoup(html_content, "lxml" if "lxml" in sys.modules else "html.parser")

        # 1. Extract & Clean Title
        title_el = soup.find("h1")
        title = title_el.text.strip() if title_el else "Unknown Title"

        # 2. Extract & Clean Price (£51.77 -> 51.77)
        price_el = soup.find("p", class_="price_color")
        price_raw = price_el.text if price_el else "£0.00"
        price_clean = DataExtractorCleaner.clean_price(price_raw)

        # 3. Extract & Clean Star Rating ("star-rating Three" -> 3)
        rating_el = soup.find("p", class_=re.compile(r"star-rating"))
        rating_stars = DataExtractorCleaner.clean_rating(rating_el.get("class", []) if rating_el else [])

        # 4. Extract Availability
        avail_el = soup.find("p", class_="instock availability")
        availability = avail_el.text.strip() if avail_el else "In stock"
        availability = re.sub(r"\s+", " ", availability)

        # 5. Extract Category from Breadcrumbs
        breadcrumb_els = soup.select("ul.breadcrumb li a")
        category = breadcrumb_els[2].text.strip() if len(breadcrumb_els) >= 3 else "General"

        # 6. Extract Product Description
        desc_header = soup.find("div", id="product_description")
        description = None
        if desc_header:
            desc_p = desc_header.find_next_sibling("p")
            if desc_p:
                description = desc_p.text.strip()

        try:
            return ScrapedProduct(
                title=title,
                price_gbp=price_clean,
                rating_stars=rating_stars,
                availability=availability,
                category=category,
                product_description=description,
                url=url
            )
        except Exception as e:
            logger.error(f"Pydantic Validation Error for URL {url}: {e}")
            return None

    @staticmethod
    def clean_price(raw_price: str) -> float:
        """Convert '£51.77' or '$12.99' to float"""
        match = re.search(r"[\d\.]+", raw_price)
        if match:
            return float(match.group(0))
        return 0.0

    @staticmethod
    def clean_rating(classes: List[str]) -> int:
        """Convert rating CSS classes like ['star-rating', 'Three'] to integer 3"""
        for cls in classes:
            cls_lower = cls.lower()
            if cls_lower in RATING_MAP:
                return RATING_MAP[cls_lower]
        return 3  # Default fallback


class CorpusExporter:
    """Exports structured records to JSONL and JSON format for RAG Corpus ingestion"""

    @staticmethod
    def export(records: List[ScrapedProduct], output_file: str = "corpus.jsonl"):
        """Save records as newline-delimited JSON (JSONL)"""
        os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else ".", exist_ok=True)

        # 1. Save as JSONL (Standard RAG Corpus format)
        with open(output_file, "w", encoding="utf-8") as f:
            for rec in records:
                f.write(rec.model_dump_json() + "\n")
        logger.info(f"[SUCCESS] Exported {len(records)} records to JSONL: {output_file}")

        # 2. Save as JSON Array (Secondary Format)
        json_output = output_file.replace(".jsonl", ".json")
        with open(json_output, "w", encoding="utf-8") as f:
            json.dump([rec.model_dump() for rec in records], f, indent=2)
        logger.info(f"[SUCCESS] Exported secondary JSON: {json_output}")


class PoliteScraperPipeline:
    """Main Orchestrator for the 5-Stage Scraping Pipeline"""

    def __init__(self, fetcher: PoliteFetcher):
        self.fetcher = fetcher

    def run(self, base_url: str, max_pages: int = 5) -> List[ScrapedProduct]:
        """Execute crawl across practice target pages"""
        logger.info(f"Starting Polite Scraper Pipeline on target: {base_url} (Limit: {max_pages} pages)")
        scraped_records: List[ScrapedProduct] = []

        # Step 1: Fetch main catalogue page
        html = self.fetcher.fetch(base_url)
        if not html:
            logger.error("Failed to fetch initial target page. Exiting pipeline.")
            return scraped_records

        # Step 2: Extract product page links
        soup = BeautifulSoup(html, "html.parser")
        product_links = []
        for article in soup.select("article.product_pod"):
            a_tag = article.select_one("h3 a")
            if a_tag and "href" in a_tag.attrs:
                href = a_tag["href"]
                # Resolve relative URL
                if "catalogue/" not in href and "catalogue/" in base_url:
                    full_url = urljoin(base_url, href)
                else:
                    full_url = urljoin("http://books.toscrape.com/catalogue/", href.replace("catalogue/", ""))
                product_links.append(full_url)

        logger.info(f"Found {len(product_links)} product URLs. Scraping up to {max_pages}...")

        # Step 3: Crawl individual product detail pages politely
        for idx, p_url in enumerate(product_links[:max_pages], start=1):
            logger.info(f"Processing Record [{idx}/{min(max_pages, len(product_links))}]: {p_url}")
            p_html = self.fetcher.fetch(p_url)
            if p_html:
                record = DataExtractorCleaner.parse_product_page(p_html, p_url)
                if record:
                    scraped_records.append(record)
                    logger.info(f"  [EXTRACTED] '{record.title}' | GBP {record.price_gbp} | {record.rating_stars} Stars")

        return scraped_records


def main():
    parser = argparse.ArgumentParser(description="Polite Web Scraper Pipeline (Task5-w5-a1)")
    parser.add_argument("--url", type=str, default="http://books.toscrape.com/", help="Base target URL")
    parser.add_argument("--limit", type=int, default=5, help="Maximum number of pages to scrape")
    parser.add_argument("--delay", type=float, default=1.0, help="Politeness sleep delay between requests in seconds")
    parser.add_argument("--output", type=str, default="corpus.jsonl", help="Output corpus filepath")
    args = parser.parse_args()

    fetcher = PoliteFetcher(delay_seconds=args.delay)
    pipeline = PoliteScraperPipeline(fetcher)
    records = pipeline.run(base_url=args.url, max_pages=args.limit)

    if records:
        CorpusExporter.export(records, output_file=args.output)
        print(f"\n[SUCCESS] Pipeline Finished! {len(records)} records saved to '{args.output}'. Ready for Week 6 RAG Corpus!")
    else:
        print("\n❌ Pipeline completed with 0 records.")


if __name__ == "__main__":
    main()
