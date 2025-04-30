# 🌐 [Digital TMP: Open Geospatial Integration of the Teotihuacan Mapping Project Data Files]

> **Purpose:** Provide a concise but informative overview of the entire project. Designed for newcomers, reviewers, or hiring managers.

## 📌 Overview
One short paragraph explaining what this project is about, its purpose, and intended impact. Use simple, clear language.

> _Example_:  
> This project integrates disparate public datasets to create a unified geospatial database for analyzing housing accessibility in urban centers.

## 🎯 Objectives
- Goal 1: ...
- Goal 2: ...
- Goal 3: ...

## 🧱 Project Architecture
This project is organized into three core phases:
1. Database Phase – Integration and design of source databases
2. GIS Phase – Digitization and georeferencing of spatial data
3. Geospatial Integration – Merging structured and spatial data

[View detailed architecture](docs/architecture.md)

## 📊 Data Sources
- Parcel shapefiles (local municipalities)
- Demographic and housing data (US Census)
- Local infrastructure data (CSV + Access DBs)

[Full metadata and dictionary](docs/data_sources.md)

## 🛠 Tools & Technologies
- Python (pandas, geopandas, SQLAlchemy)
- R (tidyverse, sf)
- PostgreSQL + PostGIS
- QGIS
- Docker

## 📈 Key Outputs
- Interactive geospatial database (PostGIS)
- Notebooks for spatial joins, queries, and EDA
- Clean, documented data layers

## 📂 Repository Structure
| Folder | Purpose |
|--------|---------|
| `phases/` | Docs, code and outputs for each project phase |
| `docs/` | Narrative project documentation |
| `report/` | Comprehensive scientific project report |
| `data/` | Raw, interim, processed and external (cloud downloaded) datasets |
| `infrastructure/` | Database schema, Docker, external file info |
| `workflows/` | Pipeline code |
| `outputs/` | Final plots, tables, models |

## 🧑‍💻 Getting Started
1. Clone this repo
2. Set up Python environment: `pip install -r requirements.txt`
3. For R, open `your-project-name.Rproj` and run `renv::restore()`
4. Download large data assets: [see this guide](infrastructure/cloud_downloads.md)

## 👤 Author
- Rudolf Cesartetti – Rudolf.Cesaretti@asu.edu | [Linked-In](https://www.linkedin.com/in/rudolf-cesaretti) | [Website](https://rcesaret.github.io/) | [GitHub](https://github.com/rcesaret) | [ASU](https://search.asu.edu/profile/2306101)
- Attribution & licensing info here.
