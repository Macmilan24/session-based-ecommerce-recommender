# src/main.py

from recommender import Recommender
from explainer import Explainer
import config

def get_explained_recommendation(start_item_id: str):
    """
    Orchestrates the full recommendation and explanation process.

    1. Gets the top recommendation using the best model.
    2. Gets a human-readable explanation for that recommendation.
    3. Prints a clean, user-facing output.
    """
    recommender = None
    explainer = None
    
    try:
        recommender = Recommender(config.NEO4J_URI, config.NEO4J_USER, config.NEO4J_PASSWORD)
        explainer = Explainer(config.NEO4J_URI, config.NEO4J_USER, config.NEO4J_PASSWORD)

        print(f"Fetching top recommendation for item '{start_item_id}'...")
        
        recommendations = recommender.get_contextual_recommendations(start_item_id, limit=1)
        
        if not recommendations:
            print("Could not find any recommendations for this item.")
            return

        top_recommendation = recommendations[0]
        
        print(f"Top recommendation found: '{top_recommendation}'")
        print("Now generating an explanation for this recommendation...")

        explanation = explainer.generate_explanation(start_item_id, str(top_recommendation))

        print("\n==============================================")
        print("    Your Personal Recommendation")
        print("==============================================")
        print(f"Because you're viewing item: {start_item_id}")
        print(f"We recommend item:           {top_recommendation}")
        print("\n  Why you might like it:")
        print(f"  \"{explanation}\"")
        print("==============================================")

    except Exception as e:
        print(f"An error occurred during the process: {e}")
        
    finally:
        if recommender:
            recommender.close()
        if explainer:
            explainer.close()


if __name__ == "__main__":
    test_start_item = "8692" 
    
    get_explained_recommendation(test_start_item)