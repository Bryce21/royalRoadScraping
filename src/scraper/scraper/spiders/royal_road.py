"""Spider for scraping RoyalRoad fiction pages."""

from datetime import datetime
from enum import Enum
from pathlib import Path
import re
from typing import Generator, Optional
from urllib.parse import urlparse

import scrapy
from scrapy.http import Response
from scrapy.selector import Selector

from scraper.loaders import RoyalRoadFictionLoader, RoyalRoadFictionReviewLoader


class PageType(str, Enum):
    """Enumeration of RoyalRoad page types."""

    FICTION = "fiction"
    AUTHOR = "author"


class RoyalRoadSpider(scrapy.Spider):
    """Spider to fetch RoyalRoad fiction pages for inspection."""

    name: str = "royal_road"
    allowed_domains: list[str] = ["royalroad.com"]
    
    # Default start URL (can be overridden via -a start_url=...)
    default_start_url: str = (
        "https://www.royalroad.com/fiction/89034/nightmare-realm-summoner"
    )

    def __init__(self, start_url: Optional[str] = None, *args, **kwargs):
        """
        Initialize the spider with optional start URL.

        Args:
            start_url: URL to start crawling from. If not provided, uses default.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(*args, **kwargs)
        # Use provided start_url or fall back to default
        url = start_url if start_url else self.default_start_url
        self.start_urls = [url]

    def parse(self, response: Response) -> Generator[dict, None, None]:
        """
        Parse the response and extract fiction data using Item Loader.

        Args:
            response: The HTTP response from the request.

        Yields:
            dict: RoyalRoadFictionItem for fiction pages, None for other page types.
        """
        # Log response status
        self.logger.info(f"Response status: {response.status}")
        
        # Determine page type
        page_type = self._determine_page_type(response.url)
        self.logger.info(f"Page type: {page_type.value}")
        
        # Save HTML to file
        output_path = self._save_html_to_file(response)
        self.logger.info(f"Saved HTML to: {output_path}")
        
        # Process fiction pages with Item Loader
        if page_type == PageType.FICTION:
            # Create selector from response and pass both to loader
            selector = Selector(response=response)
            loader = RoyalRoadFictionLoader(selector=selector, response=response)
            loader.populate_from_response()
            item = loader.load_item()
            
            # Print the item
            self.logger.info("Extracted fiction item:")
            self.logger.info(f"  Title: {item.get('title')}")
            self.logger.info(f"  Author: {item.get('author')}")
            self.logger.info(f"  URL: {item.get('url')}")
            self.logger.info(f"  Fiction ID: {item.get('fiction_id')}")
            self.logger.info(f"  Rating: {item.get('rating')}")
            self.logger.info(f"  Followers: {item.get('follower_count')}")
            self.logger.info(f"  Tags: {item.get('tags')}")
            self.logger.info(f"  Description (first 100 chars): {str(item.get('description', ''))[:100]}...")
            
            # Also print the full item dict for inspection
            self.logger.info(f"Full item: {dict(item)}")
            
            yield item
            
            # Extract reviews from fiction page
            fiction_id = item.get("fiction_id")
            if fiction_id:
                # Extract reviews from current page
                reviews = self._extract_reviews_from_page(response, fiction_id)
                for review in reviews:
                    yield review
                
                # Follow pagination links for reviews
                next_review_page = response.xpath("//a[contains(., 'Next')]/@href").get()
                if next_review_page:
                    # Pass fiction_id via meta for pagination
                    yield response.follow(
                        next_review_page,
                        callback=self.parse_reviews,
                        meta={"fiction_id": fiction_id},
                    )
        else:
            # For non-fiction pages, just log and yield nothing
            self.logger.info(f"Skipping non-fiction page type: {page_type.value}")
            yield None

    def _save_html_to_file(self, response: Response) -> Path:
        """
        Save the response HTML to a file in examples/html/ directory.

        Args:
            response: The HTTP response containing the HTML content.

        Returns:
            Path to the saved file.
        """
        # Extract fiction name from URL
        # URL format: https://www.royalroad.com/fiction/89034/nightmare-realm-summoner
        parsed_url = urlparse(response.url)
        path_parts = parsed_url.path.strip("/").split("/")
        
        # The fiction name should be the last part of the path
        fiction_name = path_parts[-1] if path_parts else "unknown"
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{fiction_name}_{timestamp}.html"
        
        # Determine path to examples/html/ directory
        # Scrapy runs from the directory containing scrapy.cfg (src/scraper/)
        # Path from spider file: scraper/spiders/royal_road.py -> scraper/ -> scraper/ -> src/scraper/
        project_root = Path(__file__).parent.parent.parent
        output_dir = project_root / "examples" / "html"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_path = output_dir / filename
        
        # Save HTML to file
        output_path.write_text(response.text, encoding="utf-8")
        
        return output_path

    def _determine_page_type(self, url: str) -> PageType:
        """
        Determine the page type based on URL structure.

        RoyalRoad URL patterns:
        - Fiction: /fiction/{id}/{slug}
        - Author/Profile: /profile/{id}/{username} or /user/{id}/{username}

        Args:
            url: The URL to analyze.

        Returns:
            PageType enum value indicating the type of page.
        """
        parsed_url = urlparse(url)
        path_parts = [part for part in parsed_url.path.strip("/").split("/") if part]

        if not path_parts:
            return PageType.FICTION

        # Check for author/profile pages: /profile/{id}/{username} or /user/{id}/{username}
        if path_parts[0] in ("profile", "user") and len(path_parts) >= 2:
            return PageType.AUTHOR

        # Check for fiction pages: /fiction/{id}/{slug}
        # Default to FICTION for any other URL structure
        if path_parts[0] == "fiction" and len(path_parts) >= 2:
            return PageType.FICTION

        # Default to FICTION for unrecognized patterns
        return PageType.FICTION

    def _extract_fiction_id_from_url(self, url: str) -> Optional[int]:
        """Extract fiction ID from RoyalRoad URL pattern /fiction/{id}/..."""
        try:
            parsed = urlparse(url)
            # Pattern: /fiction/{id}/...
            match = re.search(r"/fiction/(\d+)/", parsed.path)
            if match:
                return int(match.group(1))
        except (ValueError, AttributeError):
            pass
        return None

    def _extract_reviews_from_page(
        self, response: Response, fiction_id: int
    ) -> Generator[dict, None, None]:
        """Extract all reviews from the current page.

        Args:
            response: The HTTP response containing the page.
            fiction_id: The ID of the fiction being reviewed.

        Yields:
            dict: RoyalRoadFictionReviewItem for each review found.
        """
        review_elements = response.css(".review")
        
        if not review_elements:
            self.logger.info("No reviews found on this page")
            return

        self.logger.info(f"Found {len(review_elements)} reviews on this page")

        for review_element in review_elements:
            try:
                loader = RoyalRoadFictionReviewLoader(selector=review_element)
                loader.populate_from_review()
                # Set fiction_id
                loader.add_value("fiction_id", str(fiction_id))
                item = loader.load_item()

                # Check if all required fields are present
                required_fields = [
                    "review_id",
                    "review_title",
                    "review",
                    "by",
                    "author_id",
                    "reviewed_at_time",
                    "reviewed_at_chapter",
                    "overall_rating",
                    "fiction_id",
                ]
                missing_fields = [
                    field for field in required_fields if not item.get(field)
                ]

                if missing_fields:
                    self.logger.warning(
                        f"Skipping review due to missing required fields: {missing_fields}"
                    )
                    continue

                # Log the review item
                self.logger.info(f"Extracted review item:")
                self.logger.info(f"  Review ID: {item.get('review_id')}")
                self.logger.info(f"  Title: {item.get('review_title')}")
                self.logger.info(f"  By: {item.get('by')}")
                self.logger.info(f"  Overall Rating: {item.get('overall_rating')}")
                self.logger.info(f"  Fiction ID: {item.get('fiction_id')}")

                yield item
            except Exception as e:
                self.logger.error(f"Error extracting review: {e}", exc_info=True)
                continue

    def parse_reviews(self, response: Response) -> Generator[dict, None, None]:
        """Parse review pagination pages and extract reviews.

        Args:
            response: The HTTP response from the review pagination page.

        Yields:
            dict: RoyalRoadFictionReviewItem for each review found.
        """
        # Get fiction_id from meta or extract from URL
        fiction_id = response.meta.get("fiction_id")
        if not fiction_id:
            fiction_id = self._extract_fiction_id_from_url(response.url)
            if not fiction_id:
                self.logger.warning(
                    f"Could not extract fiction_id from URL: {response.url}"
                )
                return

        # Extract reviews from current page
        reviews = list(self._extract_reviews_from_page(response, fiction_id))
        for review in reviews:
            yield review

        # Follow pagination links
        next_page = response.xpath("//a[contains(., 'Next')]/@href").get()
        if next_page:
            self.logger.info(f"Following review pagination link: {next_page}")
            yield response.follow(
                next_page,
                callback=self.parse_reviews,
                meta={"fiction_id": fiction_id},
            )
        else:
            self.logger.info("No more review pages to follow")

