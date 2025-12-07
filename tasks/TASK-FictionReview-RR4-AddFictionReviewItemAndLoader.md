## Name: TASK-FictionReview-RR4-AddFictionReviewItemAndLoader

## Problem statement:
Agent and developer are going to define a scrapy item and loader for the reviews on the fiction page. Reviews are displayed on fiction pages and are paginated, requiring pagination handling to extract all reviews for a given fiction. Reviews should always be extracted when scraping a fiction page.

Under /examples/html there are example fiction pages available to understand the format.

### Fiction Review Item Fields:
**Required fields:**
* `review_id` (int): Unique identifier for the review
* `review_title` (str): The title/heading of the review
* `review` (str): The text content of the review
* `by` (str): The name of the reviewing author
* `author_id` (int): The ID of the reviewing author
* `reviewed_at_time` (str): ISO format datetime string of when the review was submitted
* `reviewed_at_chapter` (str): The chapter text where the reviewer submitted the review
* `overall_rating` (float): The overall rating given (can include half stars, e.g., 4.5, 5.0)
* `fiction_id` (int): The ID of the fiction being reviewed (for graph relationship)

**Optional fields** (only present if reviewer opted in):
* `style_rating` (float, optional): Style rating
* `story_rating` (float, optional): Story rating
* `grammar_rating` (float, optional): Grammar rating
* `character_rating` (float, optional): Character rating


## Planned approach:

### Technical strategy:
* **Item Definition**: Create a Scrapy Item class for fiction reviews following the same pattern as `RoyalRoadFictionItem`
  * Define all fields specified in the item fields section above
  * Include comprehensive documentation
  * Follow Python and Scrapy best practices

* **Loader Implementation**: Create an Item Loader class for extracting review data from HTML
  * Follow the same pattern as `RoyalRoadFictionLoader`
  * Extract all required and optional fields from the review HTML structure
  * Handle data type conversions (ratings to float, IDs to int, dates to ISO strings)
  * Handle optional fields gracefully (advanced ratings may not exist for all reviews)
  * Implement appropriate error handling and logging

* **Spider Integration**: Update the spider to extract and yield review items
  * Always extract reviews when scraping a fiction page (alongside the fiction item)
  * Handle pagination to get all reviews across multiple pages
  * Log if pagination fails partway through (partial extraction is acceptable)
  * If a fiction page has no reviews, yield nothing (no review items)
  * Include `fiction_id` in all review items (extract from URL or pass via meta)
  * Yield review items following Scrapy best practices

* **Error Handling**: Implement appropriate error handling
  * All required fields must be present - skip items with missing required fields
  * Handle optional fields gracefully (advanced ratings may not exist)
  * Log warnings for missing required data
  * Log if pagination fails partway through extraction
  * Validate data types

* **Note**: Metadata fields (`scraped_at` and `version`) should NOT be set by the loader - these are handled by pipelines.

### Expected output:
* A new `RoyalRoadFictionReviewItem` class that defines all the review fields
* A new `RoyalRoadFictionReviewLoader` class that extracts review data from HTML
* Updated `RoyalRoadSpider` that extracts and yields review items with pagination support
* When running the spider, reviews are printed out as JSON for verification/testing (following the same pattern from the fiction item)
* Note: Pipeline integration for storing reviews in Neo4j is a follow-up task and out of scope for this task

### Tests that can be done:
* **Manual Testing**:
  * Run spider on a fiction page with reviews and verify:
    * Reviews are extracted when scraping fiction pages
    * All reviews are extracted correctly (including pagination)
    * Review fields are populated correctly (check against HTML examples)
    * All required fields are present in extracted items
    * Optional advanced ratings are handled correctly (present/absent)
    * Data types are correct
    * `fiction_id` is correctly included in all review items
  * Run spider on a fiction page with no reviews and verify:
    * No review items are yielded
  * Test pagination failure scenarios and verify appropriate logging

* **Unit Tests** (future task):
  * Test helper functions with various input formats
  * Test loader with sample HTML fragments containing reviews
  * Test loader with reviews that have optional ratings vs. those without
  * Test pagination handling

* **Validation Tests**:
  * Verify all required fields are present in extracted items (skip items with missing required fields)
  * Verify optional fields are handled correctly (may be absent)
  * Verify data types match expected types
  * Verify ISO datetime format is correct
  * Verify ratings are within valid range (0.0 to 5.0)
  * Verify IDs are positive integers

## Implementation notes:
* Progress updates, decisions made during implementation



## Summary:
* To be completed when task is completed

### A brief summary of what was done and key things to know.