# src/evaluate.py

import pandas as pd
from tqdm import tqdm
import data_loader
from recommender import Recommender
import config

def get_existing_items(driver, item_ids: list) -> set:
    """Queries the database to see which of the given item IDs exist as nodes."""
    query = """
    UNWIND $item_ids AS check_id
    MATCH (i:Item {id: check_id})
    RETURN i.id AS existing_id
    """
    with driver.session() as session:
        result = session.run(query, item_ids=item_ids)
        return {record["existing_id"] for record in result}

def evaluate_all_strategies():
    """
    Calculates and compares the MRR for all three strategies.
    This version correctly compares integers to integers.
    """
    print("Starting comprehensive evaluation of all recommendation strategies...")
    
    recommender = Recommender(config.NEO4J_URI, config.NEO4J_USER, config.NEO4J_PASSWORD)
    
    print("Loading and splitting data...")
    sessions_df = data_loader.load_and_process_sessions()
    all_session_ids = sessions_df['visitorid'].unique()
    sample_session_ids = pd.Series(all_session_ids).sample(frac=0.3, random_state=42)
    unique_session_ids_in_sample = sample_session_ids.unique()
    train_session_ids = set(pd.Series(unique_session_ids_in_sample).sample(frac=0.9, random_state=42))
    test_session_ids = list(set(unique_session_ids_in_sample) - train_session_ids)
    test_df = sessions_df[sessions_df['visitorid'].isin(test_session_ids)]
    print(f"Isolated {len(test_session_ids)} sessions for a fair test.")

    print("Fetching all known item IDs from the graph...")
    all_item_ids_in_graph = get_existing_items(recommender.driver, sessions_df['itemid'].unique().tolist())
    print(f"Graph contains {len(all_item_ids_in_graph)} unique item nodes.")

    test_sessions = test_df.groupby('visitorid')['itemid'].apply(list).tolist()
    
    rr_standard, rr_recency, rr_contextual = [], [], []
    predictions_made = 0

    for session in tqdm(test_sessions, desc="Evaluating all strategies"):
        if len(session) < 2:
            continue
            
        for i in range(len(session) - 1):
            current_item = session[i]
            actual_next_item = session[i+1]
            
            if current_item not in all_item_ids_in_graph:
                continue

            predictions_made += 1
            
            current_item_str = str(current_item)

            recs_standard = recommender.get_recommendations(current_item_str, limit=10)
            
            rank_std = 1 / (recs_standard.index(actual_next_item) + 1) if actual_next_item in recs_standard else 0
            rr_standard.append(rank_std)
            
            recs_recency = recommender.get_recommendations_with_recency(current_item_str, limit=10)
            rank_rec = 1 / (recs_recency.index(actual_next_item) + 1) if actual_next_item in recs_recency else 0
            rr_recency.append(rank_rec)

            recs_contextual = recommender.get_contextual_recommendations(current_item_str, limit=10)
            rank_ctx = 1 / (recs_contextual.index(actual_next_item) + 1) if actual_next_item in recs_contextual else 0
            rr_contextual.append(rank_ctx)
            
    mrr_standard = sum(rr_standard) / predictions_made if predictions_made > 0 else 0
    mrr_recency = sum(rr_recency) / predictions_made if predictions_made > 0 else 0
    mrr_contextual = sum(rr_contextual) / predictions_made if predictions_made > 0 else 0
    
    recommender.close()
    
    return {
        "predictions_made": predictions_made,
        "standard_mrr": mrr_standard,
        "recency_mrr": mrr_recency,
        "contextual_mrr": mrr_contextual
    }

if __name__ == "__main__":
    results = evaluate_all_strategies()
    
    print("\n--- Final Performance Evaluation Summary ---")
    print(f"Total Predictions Made on the Test Set: {results['predictions_made']}")
    print("-" * 40)
    print(f"Strategy 1: Standard (Popularity) MRR:      {results['standard_mrr']:.4f}")
    print(f"Strategy 2: Recency-Weighted (Trending) MRR: {results['recency_mrr']:.4f}")
    print(f"Strategy 3: Contextual (Collaborative) MRR:  {results['contextual_mrr']:.4f}")
    print("-" * 40)
    print("\nEvaluation complete. This summary is the key result for your final report.")