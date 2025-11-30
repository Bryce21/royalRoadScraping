"""Scrapy Item definition for RoyalRoad fiction entries."""

import scrapy


class RoyalRoadFictionItem(scrapy.Item):
    """
    Scrapy Item representing a RoyalRoad fiction entry.

    This item contains metadata and information about a fiction story scraped
    from RoyalRoad, including title, author, description, statistics, and tags.

    Fields:
        title (str): The title of the fiction.
        author (str): The name of the author.
        url (str): The canonical URL of the fiction page.
        description (str): The synopsis/description of the fiction.
        tags (list[str]): List of genre/tag strings associated with the fiction.
        rating (float): The average rating of the fiction (as provided by RoyalRoad).
        follower_count (int): The number of followers for the fiction.
        fiction_id (int): The unique identifier for the fiction (extracted from URL).

    Metadata fields (set by pipeline):
        scraped_at (str): ISO format timestamp of when the item was scraped.
        version (int): Version number of the item schema (set to 1 by pipeline).
    """

    # Core fiction data fields
    title = scrapy.Field()
    author = scrapy.Field()
    url = scrapy.Field()
    description = scrapy.Field()
    tags = scrapy.Field()
    rating = scrapy.Field()
    follower_count = scrapy.Field()
    fiction_id = scrapy.Field()

    # Metadata fields (populated by pipeline)
    scraped_at = scrapy.Field()
    version = scrapy.Field()

