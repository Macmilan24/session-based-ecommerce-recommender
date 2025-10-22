# Smarter Session-Based E-commerce Recommender

This repository is a compact research/prototype demonstrating a "smarter" session-based recommender using a Neo4j graph. It ingests session events, item properties and a category tree to build:

- `Item`, `Session`, and `Category` nodes
- `:CONTAINS` (Session->Item), `:BELONGS_TO` (Item->Category), and `:CO_OCCURRED` (Item-Item) relationships

The `:CO_OCCURRED` edges are event-weighted and timestamped so we can rank by popularity, recency, and category-context.

---

## Quick start (what you need and where to put it)

- Python 3.9+ and Neo4j (bolt access). The code assumes Neo4j is available at `bolt://localhost:7687` unless you change `src/config.py`.
- Create a `data/` folder in the project root and add the CSVs below (the repository ignores `data/` by default to avoid committing large or sensitive datasets):

Required files and minimal schema checks (used by `src/data_loader.py`):

- `data/events.csv` — at minimum columns: `timestamp`, `visitorid`, `event`, `itemid`.
- `data/item_properties_part1.csv` and `data/item_properties_part2.csv` — concatenated; expected columns include `itemid`, `timestamp`, `value` (used to derive category id).
- `data/category_tree.csv` — expected columns: `categoryid`, `parentid`.

If you want a small demo dataset tracked, create a `data/demo/` folder and tell me — I can add proper `.gitignore` negation lines and commit the demo files.

---

## Environment setup (PowerShell)

In PowerShell (project root):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Verify the active interpreter:

```powershell
python -c "import sys; print(sys.executable)"
```

Use `conda` if preferred — just install the packages from `requirements.txt`.

---

## Local configuration and secrets (do not commit)

`src/config.py` currently contains placeholder values. Do NOT commit real credentials. Recommended options:

1) Keep `src/config.example.py` in the repo and create a local `src/config.py` (ignored by `.gitignore`).
2) Prefer environment variables for production/CI: update `src/config.py` to call `os.getenv(...)` and read secrets from the environment.

Example local `src/config.py` (safe pattern):

```py
import os

NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD', 'replace-me')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')  # optional, used by explainer
```

---

## Core commands

- Ingest data and build graph:

```powershell
python src/graph_builder.py
```

- Quick demo: fetch a top contextual recommendation + explanation (calls the explainer if configured):

```powershell
python src/main.py
```

- Evaluate strategies (computes MRR on sampled test set):

```powershell
python src/evaluate.py
```

---

## What `.gitignore` already protects

- `/data/` (no datasets checked in by default)
- Virtual envs: `.venv/`, `venv/`, etc.
- Local secret files: `src/config.py`, `config_local.py`, `.env`
- IDE/editor files and OS artifacts: `.vscode/`, `.idea/`, `.DS_Store`, `Thumbs.db`
- Neo4j local folders if you use a `neo4j/` directory for DB files

If you want me to add an explicit `data/demo/` tracked fixture, I will add the negation rules and commit the sample dataset.

---

## Troubleshooting & common fixes

- Neo4j connection refused: ensure Neo4j is running, check `NEO4J_URI` and credentials in local `src/config.py` or env vars.
- Git commit author errors: set global or repo-local Git identity with:

```powershell
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

- Explainer (LLM) errors: `src/explainer.py` uses `google.generativeai`. If you get import or API errors, either install/configure the client and set `GOOGLE_API_KEY`, or skip explainer calls by editing `src/main.py`.
- Memory problems when building item pairs: reduce `sample_fraction` in `graph_builder.ingest_data()` or ask me to implement streaming pair aggregation.

---

## Next steps I can implement for you (pick one)

- Add `src/config.example.py` and update code to prefer env vars.
- Add `docker-compose.yml` (Neo4j + a small Python service) and a tiny `data/demo/` dataset so the repo is runnable with one command.
- Make `explainer.py` gracefully degrade when the Google client or API key is missing.

Tell me which follow-up you want and I'll implement it next.

# Smarter Session-Based E-commerce Recommender

An end-to-end research/prototype repository demonstrating a "smarter" session-based recommender built on a Neo4j graph. The project ingests session events, item properties, and a category tree to create a graph enriched with event-weighted co-occurrence links. It implements multiple recommendation strategies and an LLM-backed explainer for human-facing reasons.

This update clarifies how to prepare your environment, where the data goes, and how the repository's `.gitignore` protects local and secret files.

## Quick table of contents

- What goes where (data and config)
- Environment setup (virtualenv / venv) — PowerShell commands
- Running the pipeline and examples
- What `.gitignore` covers (and why)
- Troubleshooting and next steps

## What goes where

Project root expects a `data/` folder with CSV files. These files are not included in the repository by design (see `.gitignore`). Place your CSVs here with the following filenames (these names are referenced directly by `src/data_loader.py`):

- `data/events.csv` — event log, expected columns include: `timestamp`, `visitorid`, `event`, `itemid` (the loader filters sessions with >=2 events)
- `data/item_properties_part1.csv` and `data/item_properties_part2.csv` — item metadata; loader concatenates both and uses the latest `timestamp` per `itemid` to pick the current `value` (category id)
- `data/category_tree.csv` — category relationships; expected columns: `categoryid`, `parentid`

Tip: keep a tiny sample CSV in `data/demo/` (and add an exception in `.gitignore` if you want it tracked). The repository currently ignores `/data/` to avoid accidentally committing large or PII-containing files.

## Environment setup (Windows PowerShell)

These commands create an isolated Python environment and install dependencies. Run inside the repository root (PowerShell):

# Smarter Session-Based E-commerce Recommender

An end-to-end research/prototype repository demonstrating a "smarter" session-based recommender built on a Neo4j graph. This project ingests raw session events, item properties and category hierarchies to build a graph enriched with event-weighted co-occurrence links. Multiple recommendation strategies are implemented, and an LLM-backed explainer can generate user-facing explanations for individual recommendations.

This README aims to be the single authoritative guide: quick overview, architecture, data schema, how to run the pipeline, examples, evaluation, configuration, and troubleshooting tips.

## Highlights

- Graph-based memory built from session co-occurrence using event-weighted pair scoring (views, add-to-cart, transactions).
- Three recommendation strategies:
	- Standard popularity (CO_OCCURRED weight)
	# Smarter Session-Based E-commerce Recommender

	An end-to-end research/prototype repository demonstrating a "smarter" session-based recommender built on a Neo4j graph. The project ingests raw session events, item properties and category hierarchies to build a graph enriched with event-weighted co-occurrence links. Multiple recommendation strategies are implemented, and an LLM-backed explainer can generate user-facing explanations for individual recommendations.

	This README aims to be the single authoritative guide: quick overview, architecture, data schema, how to run the pipeline, examples, evaluation, configuration, and troubleshooting tips.

	## Highlights

	- Graph-based memory built from session co-occurrence using event-weighted pair scoring (views, add-to-cart, transactions).
	- Three recommendation strategies:
		- Standard popularity (CO_OCCURRED weight)
		# Smarter Session-Based E-commerce Recommender

		An end-to-end research/prototype repository demonstrating a "smarter" session-based recommender built on a Neo4j graph. The project ingests raw session events, item properties and category hierarchies to build a graph enriched with event-weighted co-occurrence links. Multiple recommendation strategies are implemented, and an LLM-backed explainer can generate user-facing explanations for individual recommendations.

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

		## What goes where (data and config)

		Place your CSV input files in the `data/` folder (this folder is ignored by default to avoid committing large or sensitive files). Required filenames used by `src/data_loader.py`:

		- `data/events.csv` — event log. Required columns: `timestamp`, `visitorid`, `event`, `itemid`.
		- `data/item_properties_part1.csv` and `data/item_properties_part2.csv` — item metadata; both are concatenated by the loader. The loader expects `itemid`, `timestamp`, and `value` (used as category id).
		- `data/category_tree.csv` — category relationships; expected columns: `categoryid`, `parentid`.

		If you want to track a small demo dataset, add `!data/demo/` negation(s) to `.gitignore` and commit the demo CSV(s).

		## Environment setup (Windows PowerShell)

		Run these commands from the project root to create and activate a `venv`, then install requirements:

		```powershell
		python -m venv .venv
		.\.venv\Scripts\Activate.ps1
		python -m pip install -r requirements.txt
		```

		Check Python is using the venv:

		```powershell
		python -c "import sys; print(sys.executable)"
		```

		If you prefer `conda`, create a conda env and install dependencies from `requirements.txt`.

		## Local config and secrets

		- The repository includes `src/config.py` with placeholder values. You should NOT commit a config file containing real credentials.
		- Recommended patterns:
			- Rename the repo `src/config.py` to `src/config.example.py` and create a private `src/config.py` locally (this repo's `.gitignore` ignores `src/config.py`).
			- Or: use environment variables and change `src/config.py` to read from `os.environ` (recommended for CI & deployments).

		Example (local) `src/config.py`:

		```py
		import os

		NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
		NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
		NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD', 'replace-me')
		GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')  # optional
		```

		## Running the project (core commands)

		1) Build the graph and ingest data:

		```powershell
		python src/graph_builder.py
		```

		2) Example: get a contextual recommendation and an explanation:

		```powershell
		python src/main.py
		```

		3) Run evaluation (MRR across strategies):

		```powershell
		python src/evaluate.py
		```

		## What `.gitignore` protects

		Key items ignored by the repo:

		- `/data/` — prevents committing datasets and potential PII
		- virtual env folders: `.venv/`, `venv/`, etc.
		- local `src/config.py`, `config_local.py`, and `.env` — keeps credentials out of VCS
		- Neo4j database folders (if you store DB files under a `neo4j/` folder)

		Want to commit a demo dataset? Add explicit negation rules to `.gitignore` for the demo folder as described earlier.

		## Troubleshooting notes

		- Neo4j connectivity: confirm `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD` in your local `src/config.py` or environment variables. Default URI: `bolt://localhost:7687`.
		- Git commit author errors: set your git identity with `git config user.name "Your Name"` and `git config user.email "you@example.com"`.
		- Explainer failures: `src/explainer.py` uses `google.generativeai` and may require a specific client or key; set `GOOGLE_API_KEY` or disable explanation calls while debugging.
		- Memory pressure when building co-occurrence pairs: reduce `sample_fraction` in `graph_builder.ingest_data()` or implement streaming pair aggregation.

		## Developer checklist

		- [ ] Create a local `src/config.py` with your secrets (do not commit)
		- [ ] Put your CSVs into `data/` as named above
		- [ ] Activate venv and run `python src/graph_builder.py`

		## Suggested next improvements (I can implement)

		- Add `src/config.example.py` and update code to prefer env vars.
		- Add `docker-compose.yml` that boots Neo4j and a small demo python service.
		- Update `explainer.py` to degrade gracefully if the Google client or key is missing.

		Tell me which of the suggested next steps you'd like me to implement and I'll do it.

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
