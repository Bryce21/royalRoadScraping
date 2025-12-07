"""Item Loader for RoyalRoad fiction review entries."""

import logging
import re
from typing import Optional
from urllib.parse import urlparse

from itemloaders import ItemLoader
from itemloaders.processors import Join, MapCompose, TakeFirst
from w3lib.html import remove_tags

from scraper.items.royal_road_fiction_review import RoyalRoadFictionReviewItem

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
    """Convert string to int, returning None if conversion fails."""
    if not value:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def parse_star_rating(value: str) -> Optional[float]:
    """Extract float rating from star class (e.g., 'star-50' -> 5.0, 'star-30' -> 3.0, 'star-45' -> 4.5)."""
    if not value:
        return None
    # Pattern: star-{number} where number is 0-50 (representing 0.0 to 5.0 stars)
    match = re.search(r"star-(\d+)", str(value))
    if match:
        try:
            star_value = int(match.group(1))
            # Convert from 0-50 scale to 0.0-5.0 scale
            return star_value / 10.0
        except (ValueError, TypeError):
            pass
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


def extract_review_id_from_id(value: str) -> Optional[int]:
    """Extract review ID from element ID attribute (e.g., 'review-1271589' -> 1271589)."""
    if not value:
        return None
    # Pattern: review-{id}
    match = re.search(r"review-(\d+)", str(value))
    if match:
        try:
            return int(match.group(1))
        except (ValueError, TypeError):
            pass
    return None


def parse_datetime_to_iso(value: str) -> Optional[str]:
    """Convert datetime attribute to ISO format string (already in ISO format, just validate)."""
    if not value:
        return None
    # The datetime attribute is already in ISO format, just return it
    return value.strip()


def strip_html(value: str) -> str:
    """Remove HTML tags from text, preserving text content."""
    if not value:
        return value
    return remove_tags(value).strip()


class RoyalRoadFictionReviewLoader(ItemLoader):
    """Item Loader for RoyalRoad fiction review entries.

    This loader extracts and processes data from individual review elements
    on RoyalRoad fiction pages.

    Usage:
        # For a single review element
        review_selector = response.css('.review')[0]
        loader = RoyalRoadFictionReviewLoader(selector=review_selector)
        loader.populate_from_review()
        item = loader.load_item()
    """

    default_item_class = RoyalRoadFictionReviewItem
    default_output_processor = TakeFirst()

    # Review ID: extract from id attribute
    review_id_in = MapCompose(strip_whitespace, extract_review_id_from_id)
    review_id_out = TakeFirst()

    # Review title: strip whitespace
    review_title_in = MapCompose(strip_whitespace)
    review_title_out = TakeFirst()

    # Review text: strip HTML and whitespace, join multi-line
    review_in = MapCompose(strip_html, strip_whitespace)
    review_out = Join("\n")

    # Author name: strip whitespace
    by_in = MapCompose(strip_whitespace)
    by_out = TakeFirst()

    # Author ID: extract from profile URL
    author_id_in = MapCompose(strip_whitespace, extract_author_id_from_url)
    author_id_out = TakeFirst()

    # Review date: convert to ISO format
    reviewed_at_time_in = MapCompose(strip_whitespace, parse_datetime_to_iso)
    reviewed_at_time_out = TakeFirst()

    # Reviewed at chapter: strip whitespace
    reviewed_at_chapter_in = MapCompose(strip_whitespace)
    reviewed_at_chapter_out = TakeFirst()

    # Overall rating: parse star class to float
    overall_rating_in = MapCompose(strip_whitespace, parse_star_rating)
    overall_rating_out = TakeFirst()

    # Optional advanced ratings: parse star class to float
    style_rating_in = MapCompose(strip_whitespace, parse_star_rating)
    style_rating_out = TakeFirst()

    story_rating_in = MapCompose(strip_whitespace, parse_star_rating)
    story_rating_out = TakeFirst()

    grammar_rating_in = MapCompose(strip_whitespace, parse_star_rating)
    grammar_rating_out = TakeFirst()

    character_rating_in = MapCompose(strip_whitespace, parse_star_rating)
    character_rating_out = TakeFirst()

    # Fiction ID: convert to int (will be set by spider)
    fiction_id_in = MapCompose(strip_whitespace, parse_int)
    fiction_id_out = TakeFirst()

    def populate_from_review(self) -> None:
        """Populate all fields from the review element selector.

        This method extracts all fields from a single review element.
        All selectors are relative to the review element itself.
        """
        # Review ID: extract from id attribute on the review element
        review_id_attr = self.selector.attrib.get("id", "")
        if review_id_attr:
            self.add_value("review_id", review_id_attr)

        # Review title
        self.add_css("review_title", ".review-header h4.bold.font-blue-dark::text")

        # Review text: extract all text from review-inner
        self.add_css("review", ".review-content .review-inner *::text")

        # Author name and ID
        self.add_css("by", ".review-meta a[href^='/profile/']::text")
        author_url = self.selector.css(".review-meta a[href^='/profile/']::attr(href)").get()
        if author_url:
            self.add_value("author_id", author_url)

        # Review date: use datetime attribute
        self.add_css("reviewed_at_time", "time[datetime]::attr(datetime)")

        # Reviewed at chapter
        self.add_css("reviewed_at_chapter", ".review-header a[href^='/fiction/chapter/']::text")

        # Overall rating: extract from star class
        overall_star_class = self.selector.css(
            ".overall-score-container .star::attr(class)"
        ).get()
        if overall_star_class:
            self.add_value("overall_rating", overall_star_class)

        # Optional advanced ratings: use XPath to find specific ratings by label
        # Style rating
        style_xpath = (
            ".//div[@class='advanced-score']"
            "[div[@aria-label='Style Score']]"
            "//div[contains(@class, 'star')]/@class"
        )
        style_star_class = self.selector.xpath(style_xpath).get()
        if style_star_class:
            self.add_value("style_rating", style_star_class)

        # Story rating
        story_xpath = (
            ".//div[@class='advanced-score']"
            "[div[@aria-label='Story Score']]"
            "//div[contains(@class, 'star')]/@class"
        )
        story_star_class = self.selector.xpath(story_xpath).get()
        if story_star_class:
            self.add_value("story_rating", story_star_class)

        # Grammar rating
        grammar_xpath = (
            ".//div[@class='advanced-score']"
            "[div[@aria-label='Grammar Score']]"
            "//div[contains(@class, 'star')]/@class"
        )
        grammar_star_class = self.selector.xpath(grammar_xpath).get()
        if grammar_star_class:
            self.add_value("grammar_rating", grammar_star_class)

        # Character rating
        character_xpath = (
            ".//div[@class='advanced-score']"
            "[div[@aria-label='Character Score']]"
            "//div[contains(@class, 'star')]/@class"
        )
        character_star_class = self.selector.xpath(character_xpath).get()
        if character_star_class:
            self.add_value("character_rating", character_star_class)

    def load_item(self) -> RoyalRoadFictionReviewItem:
        """Load the item, validating required fields.

        Also logs warnings for missing required fields.
        """
        # Log warnings for missing required fields
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
        for field in required_fields:
            if not self.get_output_value(field):
                logger.warning(f"Missing required field: {field}")

        return super().load_item()

