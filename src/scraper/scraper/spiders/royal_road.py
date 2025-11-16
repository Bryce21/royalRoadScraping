"""Spider for scraping RoyalRoad fiction pages."""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Generator, Optional
from urllib.parse import urlparse

import scrapy
from scrapy.http import Response


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

    def parse(self, response: Response) -> Generator[None, None, None]:
        """
        Parse the response and save HTML for inspection.

        Args:
            response: The HTTP response from the request.

        Yields:
            None (this is a minimal implementation for connectivity testing)
        """
        # Log response status
        self.logger.info(f"Response status: {response.status}")
        
        # Determine page type
        page_type = self._determine_page_type(response.url)
        self.logger.info(f"Page type: {page_type.value}")
        
        # Save HTML to file
        output_path = self._save_html_to_file(response)
        self.logger.info(f"Saved HTML to: {output_path}")
        
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

