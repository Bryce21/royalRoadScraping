## Name: TASK-WriteDataNeo4j-RR5-WriteDataToNeo4j

## Problem statement:

Extend the existing RoyalRoad Scrapy crawler so that all parsed data (Fictions, Users, Reviews, and their relationships) is persisted to a Neo4j graph database through a Scrapy pipeline.

The solution must reliably write nodes and relationships to Neo4j, avoid creating duplicates, and support eventually-complete data (e.g., users referenced before their profiles are scraped).


### Data model requirements:
The graph schema consists of three main node types and their relationships:

**Nodes:**
* **Fiction** - Identified by `fiction_id` (unique identifier)
* **User** - Identified by `author_id` (unique identifier, also referred to as `user_id`)
* **Review** - Identified by `review_id` (unique identifier)

**Relationships (simple, no properties):**
* (User)-[:WROTE_FICTION]->(Fiction)
* (User)-[:WROTE_REVIEW]->(Review)
* (Review)-[:REVIEWS]->(Fiction)

**Node Properties:**
* All fields from the corresponding Scrapy items should be stored as node properties
* All nodes must include `created_at` and `updated_at` timestamp properties:
  * `created_at` - Set to `datetime()` when node is first created (ON CREATE)
  * `updated_at` - Set to `datetime()` on both creation and updates (ON CREATE and ON MATCH)

**MERGE Semantics:**
* All writes must use MERGE semantics to ensure:
  * no duplicate nodes (merged by unique identifier)
  * no duplicate relationships
* Partial nodes can be created early and updated later:
  * If a Fiction references a User that hasn't been scraped yet → create a minimal user node (id only)
  * When the full user page is scraped → update that node with all available fields

## Planned approach:
### Technical strategy:
First, we will need something to connect to neo4j that will allow writing. This should be configurable to support a locally running vs deployed env.


### 🔧 Technical Strategy

* **Prerequisites:**
    * Update `RoyalRoadFictionItem` to include `author_id` field (in addition to existing `author` name field)
    * This is required to create the WROTE_FICTION relationship using the user's unique identifier

* **Neo4j Connection Layer:**
    * Implement a connection module using the official Neo4j Python driver (latest stable version).
    * All configuration (URI, user, password, database) must come from Scrapy settings.
    * Configuration values should be read from OS environment variables (not hardcoded in settings.py).
    * Provide sensible defaults for environment variables (e.g., `neo4j://localhost:7687` for URI, `neo4j` for database).
    * Connection should open on spider start and close on spider shutdown.

* **Scrapy Pipeline for Graph Persistence:**
    * Create a new pipeline class (e.g., `Neo4jPipeline`).
    * Pipeline receives items of different types and routes them to the appropriate Cypher-writing functions.
    * Each item type (`RoyalRoadFictionItem`, `RoyalRoadFictionReviewItem`) results in:
        * A MERGE on the node (using unique identifier: `fiction_id`, `review_id`, or `author_id`)
        * Zero or more MERGE relationships
        * Creation of minimal User nodes when referenced by Fiction/Review items (if User node doesn't exist)
    * Each item write is a single transaction (one transaction per item).
    * Note: `UserItem` is future work and not part of this task.

* **Node Property Updates:**
    * Use MERGE with ON CREATE SET and ON MATCH SET patterns:
        * `ON CREATE SET` - Set `created_at = datetime()` and `updated_at = datetime()`
        * `ON MATCH SET` - Set `updated_at = datetime()`
        * `SET` - Update all other properties from the item
    * All fields from the Scrapy items should be stored as node properties.

* **Error Handling:**
    * Pipeline should fail fast if cannot connect to Neo4j (raise exception on connection failure).
    * If writing a specific item fails, log the error and continue processing other items (don't fail the entire crawl).

* **Idempotent Writes:**
    * All Cypher statements must use MERGE not CREATE.
    * Writes must be safe in any scraping order:
        * If a Fiction references a User that hasn't been scraped yet → create a minimal user node (id only).
        * When the full user page is scraped (future work) → update that node with all available fields.

* **Separation of Concerns:**
    * Scrapy spiders handle crawling + item extraction.
    * Pipeline handles only persistence logic.
    * No global graph state or caching in Scrapy.


### Expected output:

A scrapy pipeline that writes data in a neo4j relationship to a configured neo4j database.

### Tests that can be done:
* Integration tests using a real Neo4j instance (test database):
    * Test node creation with MERGE semantics (no duplicates)
    * Test relationship creation between nodes
    * Test node updates (ON MATCH SET behavior)
    * Test timestamp properties (`created_at`, `updated_at`)
    * Test minimal user node creation when referenced by Fiction
    * Test user node update when full user data is available
    * Test error handling (connection failures, invalid data)
    * Test transaction isolation (one item = one transaction)

## Implementation notes:
* Progress updates, decisions made during implementation

### Clarifications:
1. **UserItem**: UserItem is future work and not part of this task. User nodes are identified by `author_id` (also referred to as `user_id`). Only create User nodes when we have the `author_id` identifier from FictionItem or ReviewItem.

2. **RoyalRoadFictionItem Update**: Must add `author_id` field to `RoyalRoadFictionItem` to support the WROTE_FICTION relationship. The method for extracting `author_id` from fiction pages is an implementation decision.

3. **Minimal User Nodes**: When a Fiction references a User that hasn't been scraped yet, create a minimal user node with:
    * `id` (author_id) - required
    * No other fields (username extraction is deferred for now)

4. **Configuration**: Neo4j settings (URI, user, password, database) should be:
    * Defined in `settings.py` but read from OS environment variables
    * Not hardcoded in the settings file
    * Provide sensible defaults (e.g., `neo4j://localhost:7687` for URI, `neo4j` for database)
    * Example env vars: `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`, `NEO4J_DATABASE`

5. **Neo4j Driver**: Use the latest stable version of the official Neo4j Python driver.

6. **Error Handling**:
    * Connection failures: Pipeline should fail fast (raise exception)
    * Item write failures: Log error and continue processing other items

7. **Transactions**: Each item write is a single transaction (one transaction per item).

8. **Node Properties**: All fields from Scrapy items are stored as node properties, plus:
    * `created_at` - Set on node creation (ON CREATE)
    * `updated_at` - Set on both creation and updates (ON CREATE and ON MATCH)

9. **Relationships**: Simple relationships with no properties.

10. **Testing**: Use a real Neo4j instance for integration tests.



## Summary:
* To be completed when task is completed

### A brief summary of what was done and key things to know.