# src/recommender.py

from neo4j import GraphDatabase
import config
import data_loader

class Recommender:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()
        
    

    def get_recommendations(self, item_id: str, limit: int = 10) -> list[str]:
        query = """
        MATCH (currentItem:Item {id: $item_id})
        MATCH (currentItem)-[r:CO_OCCURRED]-(recommendedItem:Item)
        RETURN recommendedItem.id AS recommendation, r.weight AS score
        ORDER BY score DESC
        LIMIT $limit
        """
        with self.driver.session() as session:
            result = session.run(query, item_id=int(item_id), limit=limit)
            records = list(result)
            return [record["recommendation"] for record in records]

    def get_recommendations_with_recency(self, item_id: str, limit: int = 10, decay_rate: float = 0.05) -> list[str]:
        query = """
        WITH datetime().epochMillis AS now
        MATCH (currentItem:Item {id: $item_id})-[r:CO_OCCURRED]-(recommendedItem:Item)
        WITH recommendedItem, r.weight AS weight, 
             toFloat(now - r.last_seen) / (1000 * 3600 * 24) AS ageInDays
        WITH recommendedItem, (weight * exp(-$decay_rate * ageInDays)) AS score
        RETURN recommendedItem.id AS recommendation, score
        ORDER BY score DESC
        LIMIT $limit
        """
        with self.driver.session() as session:
            # THE FIX: Convert item_id to an integer.
            result = session.run(query, item_id=int(item_id), limit=limit, decay_rate=decay_rate)
            records = list(result)
            # The DB returns integers, so we convert them back to strings for consistency.
            return [record["recommendation"] for record in records]
    
    def get_contextual_recommendations(self, item_id: str, limit: int = 10, boost_factor: float = 1.5) -> list[str]:
        """
        Generates recommendations using a collaborative filtering approach combined
        with a contextual boost for items in the same category.
        """
        query = """
        // Part 1: Find the category of the starting item for contextual boosting
        MATCH (start_item:Item {id: $item_id})-[:BELONGS_TO]->(start_category:Category)

        // Part 2: The Collaborative Filtering traversal
        MATCH (start_item)<-[:CONTAINS]-(session:Session)
        MATCH (session)-[:CONTAINS]->(rec_item:Item)
        WHERE start_item <> rec_item

        // Part 3: Contextual Boosting with Categories
        MATCH (rec_item)-[:BELONGS_TO]->(rec_category:Category)

        // Part 4: Calculate the score
        WITH rec_item, start_category, rec_category, count(session) AS session_count
        WITH rec_item, session_count * (CASE WHEN start_category = rec_category THEN $boost_factor ELSE 1.0 END) AS score

        // Part 5: Return the final, ranked list
        RETURN rec_item.id AS recommendation, score
        ORDER BY score DESC
        LIMIT $limit
        """
        with self.driver.session() as session:
            # Note: We are back to using strings for IDs because our data loader is now consistent.
            # However, if your categories were loaded as numbers, you might need to adjust.
            # We will assume string IDs for everything for consistency.
            result = session.run(query, item_id=int(item_id), limit=limit, boost_factor=boost_factor)
            return [record["recommendation"] for record in result]

if __name__ == "__main__":
    print("Testing all three recommendation strategies...")
    
    recommender = Recommender(config.NEO4J_URI, config.NEO4J_USER, config.NEO4J_PASSWORD)
    
    # We may need a different test item, as the new graph has different connections.
    # Find a popular one with: MATCH (i:Item)-[r:CO_OCCURRED]-() RETURN i.id, r.weight ORDER BY r.weight DESC LIMIT 1
    test_item_id = "285930" # Replace if you find a better one from the query
    
    try:
        print(f"\n--- Strategy 1: Standard Recommendations (Popularity) for item: '{test_item_id}' ---")
        standard_recs = recommender.get_recommendations(test_item_id, limit=10)
        for i, rec_id in enumerate(standard_recs, 1):
            print(f"{i}. {rec_id}")

        print(f"\n--- Strategy 2: Recency-Weighted Recommendations (Trending) for item: '{test_item_id}' ---")
        recency_recs = recommender.get_recommendations_with_recency(test_item_id, limit=10)
        for i, rec_id in enumerate(recency_recs, 1):
            print(f"{i}. {rec_id}")

        print(f"\n--- Strategy 3: Contextual Recommendations (Collaborative + Category Boost) for item: '{test_item_id}' ---")
        contextual_recs = recommender.get_contextual_recommendations(test_item_id, limit=10)
        for i, rec_id in enumerate(contextual_recs, 1):
            print(f"{i}. {rec_id}")

        print("\nAnalysis: Compare the lists. The 'Contextual' list will likely surface different items by analyzing user journeys and favoring category similarity.")

    except Exception as e:
        print(f"An error occurred: {e}")
        
    finally:
        recommender.close()