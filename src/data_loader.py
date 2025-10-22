import pandas as pd
from tqdm import tqdm
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
EVENTS_FILE = os.path.join(DATA_DIR, 'events.csv')
ITEM_PROPS_PART1_FILE = os.path.join(DATA_DIR, 'item_properties_part1.csv')
ITEM_PROPS_PART2_FILE = os.path.join(DATA_DIR, 'item_properties_part2.csv')
CATEGORY_TREE_FILE = os.path.join(DATA_DIR, 'category_tree.csv')

def load_and_process_sessions() -> pd.DataFrame:
    """
    Loads the events data, filters for 'view' events, identifies sessions,
    and filters out sessions with fewer than 2 view events.

    Returns:
        pd.DataFrame: A DataFrame containing sorted, valid session data.
                      Columns: ['timestamp', 'visitorid', 'event', 'itemid']
    """
    print("Processing events.csv to create session data...")
    
    events_df = pd.read_csv(
        EVENTS_FILE, 
        dtype={'visitorid': 'int32', 'itemid': 'int32'}
    )
    
    event_counts = events_df['visitorid'].value_counts()
    
    valid_session_ids = event_counts[event_counts >= 2].index
    
    sessions_df = events_df[events_df['visitorid'].isin(valid_session_ids)]

    sessions_df = sessions_df.sort_values(by=['visitorid', 'timestamp'])

    print(f"Finished processing events. Found {len(valid_session_ids)} sessions with 2 or more events.")
    return sessions_df


def load_item_properties() -> pd.DataFrame:
    """
    Loads and concatenates the two item property files.

    Returns:
        pd.DataFrame: A DataFrame containing item properties.
    """
    print("Processing item property files...")
    
    props_df1 = pd.read_csv(ITEM_PROPS_PART1_FILE)
    props_df2 = pd.read_csv(ITEM_PROPS_PART2_FILE)

    item_props_df = pd.concat([props_df1, props_df2], ignore_index=True)
    
    print(f"Finished processing item properties. Found {item_props_df['itemid'].nunique()} unique items.")
    return item_props_df


def load_category_tree() -> pd.DataFrame:
    """
    Loads the category hierarchy data.

    Returns:
        pd.DataFrame: A DataFrame representing the category tree.
    """
    print("Loading category tree...")
    category_tree_df = pd.read_csv(CATEGORY_TREE_FILE)
    print(f"Finished loading category tree. Found {category_tree_df['categoryid'].nunique()} categories.")
    return category_tree_df


if __name__ == "__main__":
    print("Starting data loading and preprocessing...")
    
    sessions_df = load_and_process_sessions()
    item_props_df = load_item_properties()
    category_tree_df = load_category_tree()
    
    print("\nData loading and preprocessing complete.")
    
    print("\n--- Session Data Sample ---")
    print(sessions_df.head())
    print(f"\nShape of session data: {sessions_df.shape}")
    
    print("\n--- Item Properties Data Sample ---")
    print(item_props_df.head())
    print(f"\nShape of item properties data: {item_props_df.shape}")

    print("\n--- Category Tree Data Sample ---")
    print(category_tree_df.head())
    print(f"\nShape of category tree data: {category_tree_df.shape}")