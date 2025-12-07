"""Scrapy Item definition for RoyalRoad fiction review entries."""

import scrapy


class RoyalRoadFictionReviewItem(scrapy.Item):
    """
    Scrapy Item representing a RoyalRoad fiction review entry.

    This item contains information about a review for a fiction story scraped
    from RoyalRoad, including review content, author, ratings, and metadata.

    Fields:
        review_id (int): Unique identifier for the review.
        review_title (str): The title/heading of the review.
        review (str): The text content of the review.
        by (str): The name of the reviewing author.
        author_id (int): The ID of the reviewing author.
        reviewed_at_time (str): ISO format datetime string of when the review was submitted.
        reviewed_at_chapter (str): The chapter text where the reviewer submitted the review.
        overall_rating (float): The overall rating given (can include half stars, e.g., 4.5, 5.0).
        fiction_id (int): The ID of the fiction being reviewed (for graph relationship).

    Optional fields (only present if reviewer opted in):
        style_rating (float, optional): Style rating.
        story_rating (float, optional): Story rating.
        grammar_rating (float, optional): Grammar rating.
        character_rating (float, optional): Character rating.

    Metadata fields (set by pipeline):
        scraped_at (str): ISO format timestamp of when the item was scraped.
        version (int): Version number of the item schema (set to 1 by pipeline).
    """

    # Core review data fields
    review_id = scrapy.Field()
    review_title = scrapy.Field()
    review = scrapy.Field()
    by = scrapy.Field()
    author_id = scrapy.Field()
    reviewed_at_time = scrapy.Field()
    reviewed_at_chapter = scrapy.Field()
    overall_rating = scrapy.Field()
    fiction_id = scrapy.Field()

    # Optional additional ratings (only present if reviewer opted in)
    style_rating = scrapy.Field()
    story_rating = scrapy.Field()
    grammar_rating = scrapy.Field()
    character_rating = scrapy.Field()

    # Metadata fields (populated by pipeline)
    scraped_at = scrapy.Field()
    version = scrapy.Field()

