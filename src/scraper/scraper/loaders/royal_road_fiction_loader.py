"""Item Loader for RoyalRoad fiction pages."""

import logging
import re
from typing import Optional
from urllib.parse import urlparse

from itemloaders import ItemLoader
from itemloaders.processors import Identity, Join, MapCompose, TakeFirst
from w3lib.html import remove_tags

from scraper.items.royal_road_fiction import RoyalRoadFictionItem

logger = logging.getLogger(__name__)


def strip_whitespace(value: str) -> str:
    """Strip leading and trailing whitespace from a string."""
    if not value:
        return value
    return value.strip()


def parse_float(value: str) -> Optional[float]:
    """Convert string to float, returning None if conversion fails."""
    if not value:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def parse_int(value: str) -> Optional[int]:
    """Convert string to int, handling comma-separated numbers."""
    if not value:
        return None
    # Remove commas and whitespace
    cleaned = re.sub(r"[,\s]", "", str(value))
    try:
        return int(cleaned)
    except (ValueError, TypeError):
        return None


def extract_fiction_id_from_url(url: str) -> Optional[int]:
    """Extract fiction ID from RoyalRoad URL pattern /fiction/{id}/..."""
    if not url:
        return None
    try:
        parsed = urlparse(url)
        # Pattern: /fiction/{id}/...
        match = re.search(r"/fiction/(\d+)/", parsed.path)
        if match:
            return int(match.group(1))
    except (ValueError, AttributeError):
        pass
    return None


def extract_fiction_id_from_script(response) -> Optional[int]:
    """Extract fiction ID from window.fictionId script tag."""
    # Look for window.fictionId = {number};
    script_text = response.css("script::text").getall()
    for script in script_text:
        match = re.search(r"window\.fictionId\s*=\s*(\d+);", script)
        if match:
            return int(match.group(1))
    return None


def extract_author_id_from_url(url: str) -> Optional[int]:
    """Extract author ID from RoyalRoad profile URL pattern /profile/{id}."""
    if not url:
        return None
    try:
        parsed = urlparse(url)
        # Pattern: /profile/{id} or /profile/{id}/...
        match = re.search(r"/profile/(\d+)", parsed.path)
        if match:
            return int(match.group(1))
    except (ValueError, AttributeError):
        pass
    return None


def strip_html(value: str) -> str:
    """Remove HTML tags from text, preserving text content."""
    if not value:
        return value
    return remove_tags(value).strip()


class RoyalRoadFictionLoader(ItemLoader):
    """Item Loader for RoyalRoad fiction pages.

    This loader extracts and processes data from RoyalRoad fiction pages,
    preferring meta tags when available and falling back to DOM elements.

    Usage:
        loader = RoyalRoadFictionLoader(response=response)
        loader.populate_from_response()
        item = loader.load_item()
    """

    default_item_class = RoyalRoadFictionItem
    default_output_processor = TakeFirst()

    def __init__(self, *args, **kwargs):
        """Initialize the loader and store the response if provided."""
        # Store response before passing to parent
        response = kwargs.get("response", None)
        self.response = response
        
        # ItemLoader accepts response=response and converts it internally
        # But we need to ensure selector is set up properly
        # If response is provided, ItemLoader will create a selector from it
        # Call parent __init__ which will handle response=response
        super().__init__(*args, **kwargs)
        
        # After parent init, try to get response from selector if we don't have it
        if not self.response and hasattr(self, "selector") and self.selector:
            # Try to extract response from selector
            if hasattr(self.selector, "response"):
                self.response = self.selector.response
            elif hasattr(self.selector, "root"):
                # The selector's root might be the response object
                if hasattr(self.selector.root, "url"):
                    self.response = self.selector.root

    # Title: prefer meta tags, fall back to DOM
    title_in = MapCompose(strip_whitespace)
    title_out = TakeFirst()

    # Author: prefer meta tags, fall back to DOM
    author_in = MapCompose(strip_whitespace)
    author_out = TakeFirst()

    # URL: use canonical link or response URL
    url_in = MapCompose(strip_whitespace)
    url_out = TakeFirst()

    # Description: strip HTML, prefer full DOM content over truncated meta
    description_in = MapCompose(strip_html, strip_whitespace)
    description_out = Join("\n")

    # Tags: keep as list
    tags_in = MapCompose(strip_whitespace)
    tags_out = Identity()

    # Rating: convert to float
    rating_in = MapCompose(strip_whitespace, parse_float)
    rating_out = TakeFirst()

    # Follower count: convert to int, handle commas
    follower_count_in = MapCompose(strip_whitespace, parse_int)
    follower_count_out = TakeFirst()

    # Fiction ID: extract from URL or script tag
    fiction_id_in = MapCompose(strip_whitespace, parse_int)
    fiction_id_out = TakeFirst()

    # Author ID: extract from profile URL
    author_id_in = MapCompose(strip_whitespace, extract_author_id_from_url)
    author_id_out = TakeFirst()

    def populate_from_response(self) -> None:
        """Populate all fields from the response, using fallback strategies.

        This method extracts all fields from the response, preferring meta tags
        when available and falling back to DOM elements. Multiple selectors for
        the same field are processed in order, with the first match being used.
        """
        # Response should be stored in __init__, but check if we have a selector
        if not hasattr(self, "response") or not self.response:
            logger.warning("No response available for extraction - selectors may not work")
            # Continue anyway - selectors might still work if ItemLoader set them up

        # Title: prefer meta tags, fall back to DOM
        self.add_css("title", 'meta[property="twitter:title"]::attr(content)')
        self.add_css("title", 'meta[property="og:title"]::attr(content)')
        self.add_css("title", "h1.font-white::text")
        self.add_css("title", ".fic-title h1::text")

        # Author: prefer meta tags, fall back to DOM
        self.add_css("author", 'meta[property="books:author"]::attr(content)')
        self.add_css("author", ".fic-title h4 a.font-white::text")
        self.add_css("author", '.portlet-body a.font-red[href^="/profile/"]::text')

        # Author ID: extract from profile URL
        author_url = self.selector.css('.portlet-body a.font-red[href^="/profile/"]::attr(href)').get()
        if not author_url:
            author_url = self.selector.css('.fic-title h4 a.font-white[href^="/profile/"]::attr(href)').get()
        if author_url:
            self.add_value("author_id", author_url)

        # URL: use canonical link (fallback to response.url in load_item)
        self.add_css("url", 'link[rel="canonical"]::attr(href)')
        self.add_css("url", 'meta[property="og:url"]::attr(content)')

        # Description: prefer full DOM content over truncated meta
        self.add_css("description", ".description .hidden-content *::text")
        self.add_css("description", ".description::text")
        self.add_css("description", 'meta[property="og:description"]::attr(content)')

        # Tags: extract from DOM fiction-tag links
        self.add_css("tags", ".tags a.fiction-tag::text")

        # Rating: from meta tag
        self.add_css("rating", 'meta[property="books:rating:value"]::attr(content)')

        # Follower count: from statistics section
        # Use XPath to find li containing "Followers" and get next sibling
        follower_xpath = (
            "//div[contains(@class, 'fiction-stats')]"
            "//li[contains(text(), 'Followers')]"
            "/following-sibling::li[1]/text()"
        )
        self.add_xpath("follower_count", follower_xpath)

    def load_item(self) -> RoyalRoadFictionItem:
        """Load the item, handling special cases like URL and fiction_id.

        Also logs warnings for missing required fields.
        """
        # Set URL from response if not found in HTML
        if not self.get_output_value("url"):
            if hasattr(self, "response") and self.response:
                self.add_value("url", self.response.url)
            else:
                logger.warning("URL not found and no response available")

        # Set fiction_id from URL or script if not found
        if not self.get_output_value("fiction_id"):
            if hasattr(self, "response") and self.response:
                # Try extracting from URL
                fiction_id = extract_fiction_id_from_url(self.response.url)
                if fiction_id:
                    self.add_value("fiction_id", str(fiction_id))
                else:
                    # Try extracting from script tag
                    fiction_id = extract_fiction_id_from_script(self.response)
                    if fiction_id:
                        self.add_value("fiction_id", str(fiction_id))
                    else:
                        logger.warning(
                            f"Could not extract fiction_id from URL or script: {self.response.url}"
                        )
            else:
                logger.warning("Fiction ID not found and no response available")

        # Log warnings for missing required fields
        required_fields = [
            "title",
            "author",
            "url",
            "description",
            "tags",
            "rating",
            "follower_count",
            "fiction_id",
        ]
        # Note: author_id is not in required_fields as it may not always be available
        for field in required_fields:
            if not self.get_output_value(field):
                logger.warning(f"Missing required field: {field}")

        return super().load_item()

