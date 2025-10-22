# Session-Based E-commerce Recommender

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
- Explainer (LLM) errors: `src/explainer.py` uses `google.generativeai`. If you get import or API errors, either install/configure the client and set `GOOGLE_API_KEY`, or skip explainer calls by editing `src/main.py`.
- Memory problems when building item pairs: reduce `sample_fraction` in `graph_builder.ingest_data()` or ask me to implement streaming pair aggregation.

---

- Add a Docker Compose example to spin up Neo4j and a demo dataset.
- Create small unit tests and CI (GitHub Actions) that run the evaluation script on a tiny fixture dataset.
- Replace the hard-coded Google API key in `src/config.py` with an environment-variable-backed loader and update `explainer.py` to be tolerant when the key is missing.

Tell me which follow-up you'd prefer and I'll implement it.
