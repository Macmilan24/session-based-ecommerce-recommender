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
            RETURN recommendedItem.id AS recommendation, r.event_weight AS score  
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
        WITH recommendedItem, r.event_weight AS weight, 
            toFloat(now - r.last_seen) / (1000 * 3600 * 24) AS ageInDays
        WITH recommendedItem, (weight * exp(-$decay_rate * ageInDays)) AS score
        RETURN recommendedItem.id AS recommendation, score
        ORDER BY score DESC
        LIMIT $limit
        """
        with self.driver.session() as session:
            result = session.run(query, item_id=int(item_id), limit=limit, decay_rate=decay_rate)
            records = list(result)
            return [record["recommendation"] for record in records]
    
    def get_contextual_recommendations(self, item_id: str, limit: int = 10, boost_factor: float = 1.5) -> list[str]:
        """
        Generates recommendations using a collaborative filtering approach combined
        with a contextual boost for items in the same category.
        """
        # src/recommender.py - Inside the get_contextual_recommendations function

        query = """
            MATCH (start_item:Item {id: $item_id})-[:BELONGS_TO]->(start_category:Category)
            MATCH (start_item)-[r:CO_OCCURRED]-(rec_item:Item)
            WHERE r.session_count IS NOT NULL AND r.event_weight IS NOT NULL
            MATCH (rec_item)-[:BELONGS_TO]->(rec_category:Category)

            WITH rec_item, start_category, rec_category, (r.session_count * r.event_weight) AS hybrid_base_score

            WITH rec_item, hybrid_base_score * (CASE WHEN start_category = rec_category THEN $boost_factor ELSE 1.0 END) AS final_score

            RETURN rec_item.id AS recommendation, final_score AS score
            ORDER BY score DESC
            LIMIT $limit
        """
        with self.driver.session() as session:
            result = session.run(query, item_id=int(item_id), limit=limit, boost_factor=boost_factor)
            return [record["recommendation"] for record in result]

if __name__ == "__main__":
    print("Testing all three recommendation strategies...")
    
    recommender = Recommender(config.NEO4J_URI, config.NEO4J_USER, config.NEO4J_PASSWORD)
    
    test_item_id = "285930" 
    
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