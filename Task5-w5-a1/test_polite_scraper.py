"""
Unit Test Suite for Polite Web Scraper Pipeline (Task5-w5-a1)
"""

import os
import json
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from polite_scraper import (
    ScrapedProduct,
    RobotsChecker,
    PoliteFetcher,
    DataExtractorCleaner,
    CorpusExporter,
    DEFAULT_USER_AGENT
)

SAMPLE_PRODUCT_HTML = """
<!DOCTYPE html>
<html>
<body>
  <div class="product_main">
    <h1>A Light in the Attic</h1>
    <p class="price_color">£51.77</p>
    <p class="instock availability">
        <i class="icon-ok"></i>
        In stock (22 available)
    </p>
    <p class="star-rating Three">
        <i class="icon-star"></i>
    </p>
  </div>
  <ul class="breadcrumb">
    <li><a href="/">Home</a></li>
    <li><a href="/category/books_1/index.html">Books</a></li>
    <li><a href="/category/books/poetry_23/index.html">Poetry</a></li>
    <li class="active">A Light in the Attic</li>
  </ul>
  <div id="product_description">
    <h2>Product Description</h2>
  </div>
  <p>It's a hard thing to admit, but sometimes a book of poetry can change your life.</p>
</body>
</html>
"""


class TestPoliteScraper(unittest.TestCase):

    def test_price_cleaning(self):
        """Test currency conversion to float"""
        self.assertEqual(DataExtractorCleaner.clean_price("£51.77"), 51.77)
        self.assertEqual(DataExtractorCleaner.clean_price("$12.99"), 12.99)
        self.assertEqual(DataExtractorCleaner.clean_price("Price: 99.00 EUR"), 99.0)
        self.assertEqual(DataExtractorCleaner.clean_price("invalid"), 0.0)

    def test_rating_cleaning(self):
        """Test star rating class name to integer conversion"""
        self.assertEqual(DataExtractorCleaner.clean_rating(["star-rating", "One"]), 1)
        self.assertEqual(DataExtractorCleaner.clean_rating(["star-rating", "Three"]), 3)
        self.assertEqual(DataExtractorCleaner.clean_rating(["star-rating", "Five"]), 5)
        self.assertEqual(DataExtractorCleaner.clean_rating(["star-rating", "Unknown"]), 3)  # default

    def test_html_parsing(self):
        """Test full HTML extraction into Pydantic ScrapedProduct"""
        record = DataExtractorCleaner.parse_product_page(
            html_content=SAMPLE_PRODUCT_HTML,
            url="http://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"
        )
        self.assertIsNotNone(record)
        self.assertEqual(record.title, "A Light in the Attic")
        self.assertEqual(record.price_gbp, 51.77)
        self.assertEqual(record.rating_stars, 3)
        self.assertEqual(record.category, "Poetry")
        self.assertIn("poetry can change your life", record.product_description)

    def test_pydantic_schema_validation(self):
        """Test Pydantic model validation constraints"""
        valid_data = {
            "title": " Clean Title ",
            "price_gbp": 25.50,
            "rating_stars": 4,
            "availability": "In stock",
            "category": " Fiction ",
            "url": "http://example.com/book1"
        }
        product = ScrapedProduct(**valid_data)
        self.assertEqual(product.title, "Clean Title")  # stripped
        self.assertEqual(product.category, "Fiction")  # stripped
        self.assertEqual(product.rating_stars, 4)

    @patch("httpx.get")
    def test_robots_checker(self, mock_get):
        """Test robots.txt parser behavior"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "User-agent: *\nDisallow: /private/"
        mock_get.return_value = mock_response

        checker = RobotsChecker(user_agent="FlyRank-PoliteScraper/1.0")
        self.assertTrue(checker.is_allowed("http://example.com/public/page"))
        self.assertFalse(checker.is_allowed("http://example.com/private/secret"))

    def test_user_agent_header(self):
        """Test polite user agent default formatting"""
        fetcher = PoliteFetcher(delay_seconds=0.1)
        self.assertIn("FlyRank-PoliteScraper", fetcher.user_agent)
        self.assertEqual(fetcher.client.headers["User-Agent"], fetcher.user_agent)

    def test_corpus_exporter(self):
        """Test exporting records to JSONL format"""
        product = ScrapedProduct(
            title="Test Book",
            price_gbp=10.0,
            rating_stars=5,
            availability="In stock",
            category="Test",
            url="http://example.com/test"
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = os.path.join(tmpdir, "test_corpus.jsonl")
            CorpusExporter.export([product], output_file=output_file)

            self.assertTrue(os.path.exists(output_file))
            with open(output_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
                self.assertEqual(len(lines), 1)
                data = json.loads(lines[0])
                self.assertEqual(data["title"], "Test Book")
                self.assertEqual(data["rating_stars"], 5)


if __name__ == "__main__":
    unittest.main()
