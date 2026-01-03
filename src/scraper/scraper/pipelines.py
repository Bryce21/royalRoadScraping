"""Scrapy pipelines for the RoyalRoad scraper project."""

import logging
from typing import Any, Dict, Optional

from itemadapter import ItemAdapter
from neo4j import GraphDatabase

from scraper.items.royal_road_fiction import RoyalRoadFictionItem
from scraper.items.royal_road_fiction_review import RoyalRoadFictionReviewItem

logging.getLogger("neo4j").setLevel(logging.INFO)
logger = logging.getLogger(__name__)


class ScraperPipeline:
    """Default pipeline that passes items through unchanged."""

    def process_item(self, item, spider):
        return item


class Neo4jPipeline:
    """Pipeline that writes scraped items to Neo4j graph database.

    This pipeline handles:
    - Fiction nodes and WROTE_FICTION relationships
    - Review nodes, WROTE_REVIEW and REVIEWS relationships
    - Minimal User node creation when referenced
    - Idempotent writes using MERGE semantics
    - Timestamp management (created_at, updated_at)
    """

    def __init__(self, neo4j_uri: str, neo4j_user: str, neo4j_password: str, neo4j_database: str):
        """Initialize the Neo4j pipeline with connection parameters.

        Args:
            neo4j_uri: Neo4j connection URI (e.g., "neo4j://localhost:7687")
            neo4j_user: Neo4j username
            neo4j_password: Neo4j password
            neo4j_database: Neo4j database name
        """
        self.neo4j_uri = neo4j_uri
        self.neo4j_user = neo4j_user
        self.neo4j_password = neo4j_password
        self.neo4j_database = neo4j_database
        self.driver: Optional[Any] = None

    @classmethod
    def from_crawler(cls, crawler):
        """Create pipeline instance from crawler settings."""
        return cls(
            neo4j_uri=crawler.settings.get("NEO4J_URI"),
            neo4j_user=crawler.settings.get("NEO4J_USER"),
            neo4j_password=crawler.settings.get("NEO4J_PASSWORD"),
            neo4j_database=crawler.settings.get("NEO4J_DATABASE"),
        )

    def open_spider(self, spider):
        """Open Neo4j connection when spider starts."""
        try:
            self.driver = GraphDatabase.driver(
                self.neo4j_uri,
                auth=(self.neo4j_user, self.neo4j_password),
            )
            # Verify connection
            with self.driver.session(database=self.neo4j_database) as session:
                session.run("RETURN 1")
            logger.info(
                f"Connected to Neo4j at {self.neo4j_uri}, database: {self.neo4j_database}"
            )
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise

    def close_spider(self, spider):
        """Close Neo4j connection when spider closes."""
        if self.driver:
            self.driver.close()
            logger.info("Closed Neo4j connection")

    def process_item(self, item, spider):
        """Process item and write to Neo4j.

        Args:
            item: The scraped item (FictionItem or ReviewItem)
            spider: The spider that scraped the item

        Returns:
            The item (unchanged)
        """
        if not self.driver:
            logger.error("Neo4j driver not initialized")
            return item

        adapter = ItemAdapter(item)
        logger.info(f"Processing item of type {type(item)}")

        try:
            # Scrapy items are dict-like, so check for identifying fields instead of isinstance
            if adapter.get("fiction_id") is not None:
                logger.info(f"Processing FictionItem with fiction_id: {adapter.get('fiction_id')}")
                self._process_fiction_item(adapter)
            elif adapter.get("review_id") is not None:
                logger.info(f"Processing ReviewItem with review_id: {adapter.get('review_id')}")
                self._process_review_item(adapter)
            else:
                logger.warning(f"Unknown item type - no fiction_id or review_id found. Item keys: {list(adapter.keys())}")
        except Exception as e:
            logger.error(f"Error processing item {adapter.get('fiction_id') or adapter.get('review_id')}: {e}", exc_info=True)
            # Continue processing other items (don't fail the crawl)

        return item

    def _process_fiction_item(self, adapter: ItemAdapter):
        """Process a FictionItem and write to Neo4j.

        Creates:
        - Fiction node
        - User node (minimal, if author_id is available)
        - WROTE_FICTION relationship
        """
        fiction_id = adapter.get("fiction_id")
        if not fiction_id:
            logger.warning("Fiction item missing fiction_id, skipping")
            return

        author_id = adapter.get("author_id")

        with self.driver.session(database=self.neo4j_database) as session:
            # Create or update Fiction node
            fiction_props = self._extract_fiction_properties(adapter)
            logger.info(f"Writing Fiction node with id={fiction_id}, properties={list(fiction_props.keys())}")
            result = session.run(
                """
                MERGE (f:Fiction {id: $fiction_id})
                ON CREATE SET
                    f.created_at = datetime(),
                    f.updated_at = datetime()
                ON MATCH SET
                    f.updated_at = datetime()
                SET f += $properties
                RETURN f.id as id
                """,
                fiction_id=fiction_id,
                properties=fiction_props,
            )
            # Consume the result to ensure the query executes
            result.single()
            logger.info(f"Successfully wrote Fiction node: {fiction_id}")

            # Create minimal User node and relationship if author_id is available
            if author_id:
                # Create minimal User node (id only)
                session.run(
                    """
                    MERGE (u:User {id: $author_id})
                    ON CREATE SET
                        u.created_at = datetime(),
                        u.updated_at = datetime()
                    ON MATCH SET
                        u.updated_at = datetime()
                    """,
                    author_id=author_id,
                )

                # Create WROTE_FICTION relationship
                session.run(
                    """
                    MATCH (u:User {id: $author_id}), (f:Fiction {id: $fiction_id})
                    MERGE (u)-[:WROTE_FICTION]->(f)
                    """,
                    author_id=author_id,
                    fiction_id=fiction_id,
                )

            logger.info(f"Processed Fiction node: {fiction_id}")

    def _process_review_item(self, adapter: ItemAdapter):

        review_id = adapter.get("review_id")
        if not review_id:
            logger.warning("Review item missing review_id, skipping")
            return
        

        author_id = adapter.get("author_id")
        fiction_id = adapter.get("fiction_id")

        with self.driver.session(database=self.neo4j_database) as session:
            # Create or update Review node
            review_props = self._extract_review_properties(adapter)
            logger.info(f"Writing Review node with id={review_id}, properties={list(review_props.keys())}")
            result = session.run(
                """
                MERGE (r:Review {id: $review_id})
                ON CREATE SET
                    r.created_at = datetime(),
                    r.updated_at = datetime()
                ON MATCH SET
                    r.updated_at = datetime()
                SET r += $properties
                RETURN r.id as id
                """,
                review_id=review_id,
                properties=review_props,
            )
            # Consume the result to ensure the query executes
            result.single()
            logger.info(f"Successfully wrote Review node: {review_id}")

            # Create minimal User node and WROTE_REVIEW relationship if author_id is available
            if author_id:
                session.run(
                    """
                    MERGE (u:User {id: $author_id})
                    ON CREATE SET
                        u.created_at = datetime(),
                        u.updated_at = datetime()
                    ON MATCH SET
                        u.updated_at = datetime()
                    """,
                    author_id=author_id,
                )

                # Create WROTE_REVIEW relationship
                session.run(
                    """
                    MATCH (u:User {id: $author_id}), (r:Review {id: $review_id})
                    MERGE (u)-[:WROTE_REVIEW]->(r)
                    """,
                    author_id=author_id,
                    review_id=review_id,
                )

            # Create REVIEWS relationship if fiction_id is available
            if fiction_id:
                session.run(
                    """
                    MATCH (r:Review {id: $review_id}), (f:Fiction {id: $fiction_id})
                    MERGE (r)-[:REVIEWS]->(f)
                    """,
                    review_id=review_id,
                    fiction_id=fiction_id,
                )

            logger.info(f"Processed Review node: {review_id}")

    def _extract_fiction_properties(self, adapter: ItemAdapter) -> Dict[str, Any]:
        """Extract properties from FictionItem for Neo4j node.

        Excludes metadata fields and id fields (handled separately in MERGE).
        Converts to Neo4j-compatible types.

        Args:
            adapter: ItemAdapter for the FictionItem

        Returns:
            Dictionary of properties suitable for Neo4j
        """
        props = {}
        # Exclude metadata fields and id fields (id is set in MERGE clause)
        exclude_fields = {"scraped_at", "version", "fiction_id", "author_id"}
        for key, value in adapter.items():
            if key not in exclude_fields and value is not None:
                props[key] = value
        return props

    def _extract_review_properties(self, adapter: ItemAdapter) -> Dict[str, Any]:
        """Extract properties from ReviewItem for Neo4j node.

        Excludes metadata fields and id fields (handled separately in MERGE).
        Converts to Neo4j-compatible types.

        Args:
            adapter: ItemAdapter for the ReviewItem

        Returns:
            Dictionary of properties suitable for Neo4j
        """
        props = {}
        # Exclude metadata fields and id fields (id is set in MERGE clause)
        exclude_fields = {"scraped_at", "version", "review_id", "author_id", "fiction_id"}
        for key, value in adapter.items():
            if key not in exclude_fields and value is not None:
                props[key] = value
        return props
