## Name: TASK-RR-001-AddSpider-InitialFetch

## Problem statement:
The agent and developer want to add a new Scrapy spider to an existing Scrapy project. The immediate goal is to create a spider that begins at the RoyalRoad fiction page:
https://www.royalroad.com/fiction/89034/nightmare-realm-summoner

The task is only to confirm connectivity: perform a basic fetch of the page, verify the spider is registered correctly, and save or log the HTML so it can be inspected in Cursor. No parsing yet.

## Planned approach:
### Technical strategy:
* Add a new spider file within the existing project's `spiders/` directory.
* Define `name`, `allowed_domains`, and `start_urls` following standard Scrapy conventions.
* Implement a minimal `parse()` method that:
  - Logs the response status (should be 200)
  - Saves the raw HTML to a local file
  - Confirms the spider is wired correctly within the project
* Defer data extraction for future tasks.
* Use type hints throughout the spider code (per project standards).
* Use default Scrapy logging.

### Expected output:
* Running `scrapy crawl royal_road` should:
  - Fetch the RoyalRoad page successfully
  - Print/log HTTP 200 status
  - Save an HTML file to `examples/html/` directory (e.g. `nightmare_realm_summoner_20241201_143022.html` - fiction name + timestamp)
  - Contain the full HTML of the fiction page for inspection

### Clarifications:
1. **HTML file location**: Save HTML files under `examples/html/` directory within the scraper project.
2. **Spider name**: Use `royal_road` (not `royalroad_fiction`) since there will be multiple page types.
3. **HTML filename**: Use fiction name + timestamp format (e.g. `nightmare_realm_summoner_20241201_143022.html`).
4. **Type hints**: Yes, include type hints throughout the spider code.
5. **Logging**: Use default Scrapy logging.

## Tests that can be done:
* Run the spider and verify it completes with no errors.
* Check that `response.status` logged from `parse()` equals 200.
* Inspect the generated HTML file for known markers such as the fiction title or summary.
* Run `scrapy list` and confirm `royal_road` appears.
* Add/attempt a non-RoyalRoad link in the spider to confirm `allowed_domains` behavior.

## Implementation notes:
* No Scrapy settings changes are required for this task; defaults are acceptable.
* RoyalRoad generally allows crawling; ensure `ROBOTSTXT_OBEY` remains true for now.
* If HTML is truncated or missing, verify user-agent and middleware.
* Keep implementation minimal; do not extract structured fields yet.

## Summary:
*To be completed when task is completed.*

### A brief summary of what was done and key things to know.
