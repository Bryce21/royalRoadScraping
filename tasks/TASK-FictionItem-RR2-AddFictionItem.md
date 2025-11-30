## Name: TASK-RR-001-DefineScrapyItemForFiction

## Problem statement:
The agent and developer need a structured way to store scraped fiction metadata from RoyalRoad. Although the spider that fetches the page data already exists, it currently lacks a strongly typed Scrapy `Item` definition to ensure consistent fields, validation, and clean output formatting. The goal is to define a Scrapy `Item` class representing a RoyalRoad fiction entry (title, author, synopsis, statistics, etc.) so the spider and pipelines can rely on consistent structure.
This item will have some initial data - more fields will be added as needed.

Example data of what the royal road fiction response type looks like are stored under /examples/html/.

## Planned approach:
### Technical strategy:
* Create a folder structure for items: create an `items/` directory with an `__init__.py` file.
* Create a new Scrapy `Item` class (e.g., `RoyalRoadFictionItem`) in `items/royal_road_fiction.py`.
* Delete the placeholder `ScraperItem` class from the existing `items.py` file.
* Add comprehensive class documentation (docstring) describing the Item's purpose and documenting field types.
* Define fields typically extracted from a RoyalRoad fiction page:
  - `title` (string, required)
  - `author` (string, required)
  - `url` (string, required)
  - `description` (string, required)
  - `tags` (list of strings, required)
  - `rating` (float, required)
  - `follower_count` (integer, required)
  - `last_updated` (string, required - format as provided by RoyalRoad)
  - `fiction_id` (integer, required - extracted from URL)

  Additional metadata:
  - `scraped_at` (string, required - ISO format timestamp, set in pipeline per Scrapy best practices)
  - `version` (integer, required - set to 1 in pipeline per Scrapy best practices)

* Use `scrapy.Field()` for each field.
* Use Python naming conventions (snake_case) for all field names.
* Order fields logically: core fiction data fields first, then metadata fields.
* All fields are marked as required for now. Fields can be updated to optional if/when issues are discovered during implementation.
* Metadata fields (`scraped_at` and `version`) will be populated by a pipeline, not set in the Item class or spider.
* Add a comprehensive docstring to the class that:
  - Describes the Item's purpose (representing a RoyalRoad fiction entry)
  - Documents the expected type for each field
  - Notes which fields are set by pipelines vs. the spider
* Ensure naming aligns with the spider's output to avoid mismatches.
* Optionally add processors later in pipelines.
* Update the spider to return an instance of the new `Item` object instead of raw dicts if needed.

### Expected output:
* A new `items/` directory structure:
  - `items/__init__.py` - exports the `RoyalRoadFictionItem` class
  - `items/royal_road_fiction.py` - contains the `RoyalRoadFictionItem` class definition
* The `RoyalRoadFictionItem` class with:
  - Comprehensive docstring documenting purpose and field types
  - All relevant item fields defined using `scrapy.Field()`
  - Fields ordered logically (core data first, then metadata)
* The placeholder `ScraperItem` class removed from the original `items.py` file.

### Clarifications:
1. **Field naming**: Use Python snake_case convention (e.g., `follower_count` not `followerCount`).
2. **Data types**:
   - `tags`: list of strings
   - `rating`: float (as provided by RoyalRoad)
   - `follower_count`: integer
   - `last_updated`: string (format as provided by RoyalRoad)
   - `scraped_at`: ISO format string
   - `fiction_id`: integer (extracted from URL)
3. **Metadata fields**: `version` and `scraped_at` should be set in a pipeline (per Scrapy best practices), not as defaults in the Item class definition or in the spider. The Item class should define these fields but leave them unset initially.
4. **Field requirements**: All fields are marked as required initially. Fields can be updated to optional if/when issues are discovered during implementation.
5. **Additional fields**: Include `fiction_id` extracted from the URL (e.g., 89034 from `/fiction/89034/nightmare-realm-summoner`).

