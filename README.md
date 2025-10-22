# Smarter Session-Based E-commerce Recommender

An end-to-end research / prototype repository demonstrating a "smarter" session-based recommender built on a Neo4j graph. This project ingests raw session events, item properties and category hierarchies to build a graph enriched with event-weighted co-occurrence links. Multiple recommendation strategies are implemented, and an LLM-backed explainer can generate user-facing explanations for individual recommendations.

This README aims to be the single authoritative guide: quick overview, architecture, data schema, how to run the pipeline, examples, evaluation, configuration, and troubleshooting tips.

## Highlights

- Graph-based memory built from session co-occurrence using event-weighted pair scoring (views, add-to-cart, transactions).
- Three recommendation strategies:
	- Standard popularity (CO_OCCURRED weight)
	- Recency-weighted (decay applied to last_seen)
	- Contextual collaborative recommendation with category boosting
- LLM-powered explanations (uses Google Generative API) to create friendly, human-readable reasons for recommendations.
- Small, readable codebase ideal for research, demos, or as a foundation for production prototypes.

## Repository Structure

- `data/` — CSV inputs expected by the pipeline
	- `events.csv` — raw event log (visitorid, timestamp, itemid, event, ...)
	- `item_properties_part1.csv` and `item_properties_part2.csv` — item attributes (including category assignments)
	- `category_tree.csv` — category hierarchy (categoryid, parentid)
- `src/` — implementation
	- `config.py` — connection strings and API keys
	- `data_loader.py` — CSV loading and pre-processing helpers
	- `graph_builder.py` — builds the Neo4j graph and ingests sessions, items, categories, and weighted CO_OCCURRED edges
	- `recommender.py` — three recommendation strategies and utilities
	- `explainer.py` — LLM integration to produce human explanations (requires a Google API key)
	- `evaluate.py` — evaluation harness to compute MRR across strategies
	- `main.py` — small orchestration script showing an end-to-end example (recommend + explain)
- `requirements.txt` — Python dependencies
- `report/report.md` — (project notes / placeholder)

## Quick Conceptual Flow

1. Load and preprocess events and item metadata using `src/data_loader.py`.
2. Build the graph with `src/graph_builder.py`:
	 - Create `Item`, `Session`, and `Category` nodes.
	 - Create `:CONTAINS` edges (Session -> Item) with step and timestamp.
	 - Create `:BELONGS_TO` edges (Item -> Category).
	 - Create undirected `:CO_OCCURRED` edges between co-occurring items with a `weight` and `last_seen` timestamp, where weights are aggregated from session-level event scores.
3. Use `src/recommender.py` to query Neo4j for recommendations using multiple strategies.
4. Optionally call `src/explainer.py` to generate an LLM-based sentence explaining the recommendation.

## Installation

Prerequisites:

- Python 3.9+ (recommended)
- Neo4j 4.x/5.x running and accessible (default: bolt://localhost:7687)
- A Google Generative API key to use the explainer (optional)

Install Python dependencies:

```powershell
python -m pip install -r requirements.txt
```

Set up Neo4j (local quickstart):

1. Download and run Neo4j Desktop or use Docker:

```powershell
# Docker example
docker run --publish=7474:7474 --publish=7687:7687 --env NEO4J_AUTH=neo4j/test neo4j:5
```

2. Update `src/config.py` with the correct credentials (or set env vars and adapt code):

```py
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "your-password"
GOOGLE_API_KEY = "your-google-api-key"  # optional
```

## How to run

1. Build the graph (this ingests data and creates the weighted co-occurrence edges):

```powershell
python src/graph_builder.py
```

This will:

- Clear the Neo4j database
- Create unique constraints on Item, Session, Category
- Sample sessions (defaults to 30% of sessions) and build train/test split
- Ingest categories, sessions, items, BELONGS_TO and CONTAINS edges
- Create CO_OCCURRED edges with event-weighted aggregated weights and last_seen timestamps

2. Quick recommendation example (with generated explanation):

```powershell
python src/main.py
```

The script uses `Recommender` to fetch the top contextual recommendation for a hard-coded item id and then calls the `Explainer` to generate a one-line explanation.

3. Run evaluation to compute MRR for all strategies:

```powershell
python src/evaluate.py
```

## Configuration and Tuning

- `graph_builder.ingest_data(sample_fraction=0.3, test_set_fraction=0.1)` controls dataset sampling and train/test split.
- `graph_builder._build_weighted_cooccurrence` uses event weights: views=1, addtocart=5, transaction=10. Tweak as needed.
- `recommender.get_recommendations_with_recency(..., decay_rate=0.05)` controls how quickly item influence decays with time.
- `recommender.get_contextual_recommendations(..., boost_factor=1.5)` controls how much category-similarity boosts a candidate.

## Data schema notes

- events.csv is expected to contain at least these columns: `timestamp`, `visitorid`, `event`, `itemid`.
- item_properties CSVs must have `itemid`, `timestamp`, and `value` where `value` maps to a category id for that item (the loader chooses the latest timestamp per item).
- category_tree.csv must contain `categoryid` and `parentid` so the project can build a category hierarchy.

## Implementation details (useful internals for contributors)

- Graph ingestion is batched (default 5000 rows for sessions, 20000 for co-occurrence pairs) to avoid overloading Neo4j.
- CO_OCCURRED relationships are undirected in the ingestion (pattern: MERGE (a)-[r:CO_OCCURRED]-(b)). Each pair accumulates `weight` and updates `last_seen` to the most recent timestamp.
- Session-level scoring aggregates event weights across unique items in a session so aggressive events (transactions) boost co-occurrence stronger than plain views.

## Troubleshooting

- Neo4j connection errors: verify `src/config.py` values and ensure Neo4j is running and reachable on the specified bolt URI and port.
- Large memory usage during co-occurrence generation: the ingestion pipeline collects pair lists in memory. If your dataset is large, lower `sample_fraction` or implement an on-disk streaming approach.
- LLM errors in `explainer.py`: ensure `GOOGLE_API_KEY` is valid and has the correct permissions. The explainer uses `google.generativeai` and the `gemini-2.5-flash` model; network and API quota issues will manifest as exceptions.

## Reproducibility and Tests

- The code uses fixed random seeds where sampling happens (`random_state=42`) for reproducible small-scale experiments.
- For lightweight verification: after ingesting, use Neo4j Browser to run the following queries to inspect nodes and relationships:

```cypher
MATCH (i:Item)-[r:CO_OCCURRED]-() RETURN i.id, r.weight, r.last_seen ORDER BY r.weight DESC LIMIT 10;
MATCH (s:Session)-[:CONTAINS]->(i:Item) RETURN count(s), i.id LIMIT 5;
```

## Security and privacy notes

- This repository is a research prototype. It expects raw event logs which may contain PII. Apply appropriate anonymization before using production data.
- The default `config.py` contains placeholders — never commit real secrets to version control. Prefer environment variables for deployment.

## Next steps and ideas (quick wins)

- Add unit tests for `data_loader` and `recommender` logic (simple fixtures with tiny CSVs).
- Stream co-occurrence pair generation to avoid high memory peaks for large datasets.
- Add Docker Compose with Neo4j and a small test dataset to make demos reproducible.
- Add a lightweight web UI to interactively query an item and see recommendations + explanations.

## License & Attribution

This project is a learning and prototyping artifact. Adapt licensing as needed for your organization. No external data was bundled here; ensure you have rights to use any datasets you ingest.

----

If you'd like, I can:

- Add a Docker Compose example to spin up Neo4j and a demo dataset.
- Create small unit tests and CI (GitHub Actions) that run the evaluation script on a tiny fixture dataset.
- Replace the hard-coded Google API key in `src/config.py` with an environment-variable-backed loader and update `explainer.py` to be tolerant when the key is missing.

Tell me which follow-up you'd prefer and I'll implement it.
