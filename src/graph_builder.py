# src/graph_builder.py

import pandas as pd
from neo4j import GraphDatabase
from tqdm import tqdm
from itertools import combinations
import data_loader
import config

class GraphBuilder:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def run_query(self, query, parameters=None):
        with self.driver.session() as session:
            result = session.run(query, parameters)
            return [record for record in result]

    def clear_database(self):
        print("Clearing the database...")
        self.run_query("MATCH (n) DETACH DELETE n")

    def create_constraints(self):
        print("Creating constraints...")
        self.run_query("CREATE CONSTRAINT IF NOT EXISTS FOR (i:Item) REQUIRE i.id IS UNIQUE")
        self.run_query("CREATE CONSTRAINT IF NOT EXISTS FOR (s:Session) REQUIRE s.id IS UNIQUE")
        self.run_query("CREATE CONSTRAINT IF NOT EXISTS FOR (c:Category) REQUIRE c.id IS UNIQUE")

    def ingest_data(self, sessions_df, category_tree_df, sample_fraction=0.3, test_set_fraction=0.1):
        print(f"Sampling the dataset to use {sample_fraction:.0%} of sessions...")
        all_session_ids = sessions_df['visitorid'].unique()
        sample_session_ids = pd.Series(all_session_ids).sample(frac=sample_fraction, random_state=42)
        sampled_sessions_df = sessions_df[sessions_df['visitorid'].isin(sample_session_ids)]
        print(f"Sampled down to {len(sample_session_ids)} sessions.")

        print(f"Splitting sessions into training and test sets...")
        unique_session_ids = sampled_sessions_df['visitorid'].unique()
        train_session_ids = pd.Series(unique_session_ids).sample(frac=(1 - test_set_fraction), random_state=42)
        train_sessions_df = sampled_sessions_df[sampled_sessions_df['visitorid'].isin(train_session_ids)]
        
        self._ingest_categories(category_tree_df)
        self._ingest_sessions_and_items(train_sessions_df)
        self._build_weighted_cooccurrence(train_sessions_df)

    def _ingest_categories(self, category_tree_df):
        print("Ingesting categories...")
        query = """
        UNWIND $rows AS row
        MERGE (c:Category {id: row.categoryid})
        WITH c, row WHERE row.parentid IS NOT NULL
        MERGE (p:Category {id: row.parentid})
        MERGE (p)-[:PARENT_OF]->(c)
        """
        rows = category_tree_df.dropna().to_dict('records')
        self.run_query(query, parameters={'rows': rows})

    def _ingest_sessions_and_items(self, train_sessions_df):
        """
        This function now correctly ingests items AND links them to their category.
        """
        print("Ingesting sessions, items, :CONTAINS, and :BELONGS_TO relationships...")
        
        item_props_df = data_loader.load_item_properties()
        item_to_category = item_props_df.sort_values('timestamp').groupby('itemid').last()['value']
        
        train_sessions_df['categoryid'] = train_sessions_df['itemid'].map(item_to_category)
        train_sessions_df.dropna(subset=['categoryid'], inplace=True)

        query = """
        UNWIND $batch AS event
        MERGE (s:Session {id: event.visitorid})
        MERGE (i:Item {id: event.itemid})
        MERGE (c:Category {id: event.categoryid})
        MERGE (s)-[r:CONTAINS]->(i)
        ON CREATE SET r.step = event.step, r.timestamp = event.timestamp
        
        MERGE (i)-[:BELONGS_TO]->(c)
        """
        
        train_sessions_df['step'] = train_sessions_df.groupby('visitorid').cumcount() + 1
        batch_size = 5000 
        for start in tqdm(range(0, len(train_sessions_df), batch_size), desc="Ingesting session batches"):
            end = min(start + batch_size, len(train_sessions_df))
            batch_df = train_sessions_df.iloc[start:end]
            batch_data = batch_df.to_dict('records')
            self.run_query(query, parameters={'batch': batch_data})

    def _build_weighted_cooccurrence(self, train_sessions_df):
        """
        Builds co-occurrence relationships with weights derived from event types.
        This is the core of the "smarter" graph memory.
        """
        print("Generating event-weighted co-occurrence pairs from session data...")
        
        event_weights = {'view': 1, 'addtocart': 5, 'transaction': 10}
        train_sessions_df['event_score'] = train_sessions_df['event'].map(event_weights)

        session_groups = train_sessions_df.groupby('visitorid').agg(
            item_list=('itemid', lambda x: list(set(x))),
            session_score=('event_score', 'sum'),
            max_timestamp=('timestamp', 'max')
        ).reset_index()

        all_pairs = []
        for _, row in tqdm(session_groups.iterrows(), total=len(session_groups), desc="Generating pairs"):
            if len(row['item_list']) < 2:
                continue
            for item_a, item_b in combinations(row['item_list'], 2):
                all_pairs.append({
                    'item_a': item_a,
                    'item_b': item_b,
                    'score_to_add': row['session_score'],
                    'timestamp': row['max_timestamp']
                })
        
        pairs_df = pd.DataFrame(all_pairs)
        print(f"Generated {len(pairs_df)} weighted co-occurrence pairs. Now ingesting into the graph...")

        query = """
        UNWIND $pairs AS pair
        MATCH (a:Item {id: pair.item_a})
        MATCH (b:Item {id: pair.item_b})

        MERGE (a)-[r:CO_OCCURRED]-(b)

        ON CREATE SET r.event_weight = pair.score_to_add,
                    r.session_count = 1,
                    r.last_seen = pair.timestamp
        ON MATCH SET r.event_weight = r.event_weight + pair.score_to_add,
                    r.session_count = r.session_count + 1,
                    r.last_seen = pair.timestamp
        """
        
        batch_size = 20000
        for start in tqdm(range(0, len(pairs_df), batch_size), desc="Ingesting co-occurrence batches"):
            end = min(start + batch_size, len(pairs_df))
            batch_data = pairs_df.iloc[start:end].to_dict('records')
            self.run_query(query, parameters={'pairs': batch_data})

if __name__ == "__main__":
    print("Starting Recommender: Enriching the Graph...")
    
    builder = GraphBuilder(config.NEO4J_URI, config.NEO4J_USER, config.NEO4J_PASSWORD)
    builder.clear_database()
    builder.create_constraints()
    
    sessions_df = data_loader.load_and_process_sessions()
    category_tree_df = data_loader.load_category_tree()
    
    builder.ingest_data(sessions_df, category_tree_df)
    
    builder.close()
    
    print("\nGraph enrichment complete! The :CO_OCCURRED relationships now have event-weighted scores.")