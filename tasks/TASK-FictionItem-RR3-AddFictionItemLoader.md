## Name: TASK-RR-002-CreateItemLoaderForRoyalRoadFiction

## Problem statement:
The agent and developer need a structured, reusable, and consistent way to transform the raw HTML from RoyalRoad fiction pages into a properly populated `RoyalRoadFictionItem`. Although the item type has been defined, the current spider logic would require repetitive or manual field extraction. Creating an Item Loader allows centralized handling of extraction, cleaning, normalization, and output formatting for all fields pulled from RoyalRoad’s HTML structure. This reduces code duplication, improves consistency, and simplifies the spider.

To understand the html structure of the fiction page examples have been stored under /examples/html.


## Planned approach:
### Technical strategy:
* Create a new `loaders/` directory structure: create a `loaders/` directory with an `__init__.py` file.
* Implement a custom Item Loader class (e.g., `RoyalRoadFictionLoader`) in `loaders/royal_road_fiction_loader.py`.
* Set `default_item_class` to `RoyalRoadFictionItem`.
* Define input and output processors using `TakeFirst`, `Join`, and/or minimal custom cleaning functions.
* Use CSS selectors as the primary extraction method (following Scrapy best practices).
* Support extraction patterns based on RoyalRoad HTML structure:
  - Prefer meta tags for data extraction when available (more reliable)
  - Fall back to DOM elements when meta tags are not available
* Handle data type conversions:
  - `rating`: Convert string to float
  - `follower_count`: Convert string to int (handle comma-separated numbers)
  - `fiction_id`: Extract from URL and convert to int
  - `tags`: Keep as list (use `Identity` or `MapCompose` processor)
  - `description`: Strip HTML tags to produce plain text
* Implement error handling:
  - Handle missing fields gracefully
  - Log warnings when expected selectors don't match
* Replace direct dictionary or manual field assignment in the spider with the new Item Loader.
* Ensure the loader takes the response object so relative selectors work cleanly.
* Note: Metadata fields (`scraped_at` and `version`) should NOT be set by the loader - these are handled by pipelines.

### Expected output:
* A new `loaders/` directory structure:
  - `loaders/__init__.py` - exports the `RoyalRoadFictionLoader` class
  - `loaders/royal_road_fiction_loader.py` - contains the `RoyalRoadFictionLoader` class definition
* A Python class implementing a fully configured Item Loader for RoyalRoad fiction pages.
* The loader will:
  - Populate all fields defined in `RoyalRoadFictionItem` (excluding metadata fields set by pipelines)
  - Normalize text (strip whitespace, join description lines, take first values)
  - Convert data types appropriately (float for rating, int for follower_count and fiction_id)
  - Strip HTML from description field
  - Convert list fields appropriately (e.g., `tags` remains a list while most other fields use `TakeFirst`)
  - Handle missing fields gracefully with appropriate logging
  - Provide a clean `load_item()` result consumed by the spider
* The spider will use this loader to produce consistent, validated item objects with minimal extraction code inside `parse()`.

### Clarifications:
1. **File structure**: Use `scraper/loaders/` directory to match the existing `scraper/items/` and `scraper/spiders/` structure.
2. **Selector strategy**: Use CSS selectors as the primary method (following Scrapy best practices).
3. **Description format**: Strip HTML from description to produce plain text.
4. **Data extraction priority**: Prefer meta tags when available, fall back to DOM elements.
5. **Error handling**: Implement graceful handling of missing fields with appropriate logging.
6. **Metadata fields**: `scraped_at` and `version` should NOT be set by the loader - these are handled by pipelines.
7. **Testing**: Testing will be handled in a separate follow-up task.
