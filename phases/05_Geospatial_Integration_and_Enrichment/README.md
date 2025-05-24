
# Phase [05]: [Phase Title]

> **Purpose**: Serve as a self-contained summary for each phase of your project—especially helpful for onboarding, documentation, or portfolio readers.

## 🎯 Objective
Brief paragraph on the purpose of this phase.

> _Example_:  
> This phase focuses on ingesting and standardizing heterogeneous tabular data from CSV and Access sources to create a unified relational schema in PostgreSQL.

## 📊 Data Inputs
| File | Description | Format | Location |
|------|-------------|--------|----------|
| `property.csv` | Parcel data | CSV | `data/raw/` |
| `infra.mdb` | Infrastructure metadata | Access | external |

## ⚙️ Workflows Executed

| Notebook/Script | Description |
|-----------------|-------------|
| `notebooks/ingest_data.ipynb` | Cleans and merges CSV tables |
| `R/normalize_infra.R` | Processes MS Access DB exports |
| `python/load_to_postgres.py` | Pushes to PostgreSQL (via SQLAlchemy) |

## 🛠 Tools & Techniques
- Python (`pandas`, `sqlalchemy`)
- R (`readxl`, `tidyverse`)
- PostgreSQL
- Docker (for local DB)

## 📤 Outputs Produced

| Output | Description | Location |
|--------|-------------|----------|
| `cleaned_parcels.csv` | Joined parcel + zoning | `data/processed/` |
| `schema.sql` | DB schema | `infrastructure/db/` |

## 🧠 Reflections
Short notes on any issues, surprises, or key decisions made.

## 🔗 Next Phase
[Phase 04: PHASE 4 NAME](../PHASE4_NAME/README.md)
