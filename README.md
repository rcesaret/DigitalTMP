# 🌐 Digital TMP: Open Geospatial Integration of the Teotihuacan Mapping Project Data Files

> **Purpose:** A comprehensive modernization and digital integration initiative transforming the Teotihuacan Mapping Project’s legacy archaeological datasets into a unified, reproducible, and open-access geospatial research infrastructure, supporting both technical and non-technical audiences.

---

## 📌 Overview

The **Digital TMP** Integration Initiative is a comprehensive data science and engineering project aimed at modernizing and unifying the legacy datasets of the landmark **Teotihuacan Mapping Project (TMP)**, originally led by René Millon in the 1960s.  The TMP represents the only full-surface archaeological survey ever conducted for the ancient city of Teotihuacan, encompassing over 5,000 surface collection units across approximately 37.5 square kilometers. Despite its legacy as the empirical foundation of decades of Mesoamerican research, the TMP dataset remains fragmented across obsolete file formats, incompatible schemas, and spatial systems that prevent integration with modern digital tools.

This initiative transforms the TMP's fragmented analog and digital records—spanning over 50 years of research and multiple database generations—into a unified, reproducible, accurate, well-documented, and open-access geospatial research infrastructure. To accomplish this, the Digital TMP project executes a structured, eight-phase digital transformation pipeline that systematically converts analog archives and legacy software outputs into a unified PostgreSQL/PostGIS platform. The outcome is a modular, reproducible, and open-access geospatial database supporting SQL-based queries, modern GIS formats, and spatial analyses across artifact, architectural, and typological datasets. By systematically analyzing, transforming, integrating, and archiving the TMP's diverse digital assets, this project seeks to unlock their full scholarly potential for future generations of researchers, enabling new forms of data-driven inquiry into the urbanism, society, and history of one of the ancient world's most significant cities.

## 🎯 Key Objectives

- **Integrate Legacy Datasets**: Merge disparate TMP databases (DF8, DF9, DF10, REANS2) into a unified spatial database with schema harmonization and entity key alignment.
- **Complete Spatial Digitization**: Digitize and georeference all archaeological, environmental, and modern features from 1:2,000 TMP base maps using high-precision georeferencing workflows.
- **Ensure Data Quality and Validation**: Implement automated data quality frameworks to ensure robust, reliable, and reproducible datasets.
- **Comprehensive Documentation**: Develop structured metadata and detailed documentation to facilitate data interpretation and reuse.
- **Enable Open Access**: Publish the finalized spatial database through tDAR, interactive WebGIS platforms, and comprehensive tutorials for diverse user communities.
- **Support Future Research**: Provide high-quality spatial base layers for excavation planning, comparative urbanism studies, and integration with modern geophysical surveys.
- **Establish Extensible Infrastructure**: Create a scalable platform for integrating future TMP excavations, drone photogrammetry, and INAH archival datasets.
- **Enhance Digital Scholarship**: Produce curated datasets and reproducible workflows supporting teaching in archaeology, GIS, and digital humanities.

## 📑 Navigating the Documentation

This repository contains a comprehensive suite of documentation. To find what you need, please consult the following guide:

- **`README.md` (This file):** For a high-level project summary and immediate setup instructions.
- **`PLANNING.md`:** For the detailed, phase-by-phase operational plan intended for execution by the Windsurf "Cascade" AI agent.
- **`docs/overview.md`:** For a complete understanding of the project's vision, goals, scope, and requirements (The Project's PRD).
- **`docs/architecture.md`:** For the high-level system blueprint, including component diagrams, data flow, and non-functional architecture (Security, Performance).
- **`docs/technical_specs.md`:** For granular technical details, including the full technology stack, design patterns, and implementation specifications.
- **`docs/glossary.md`:** For definitions of all project-specific terminology, acronyms, and domain concepts.
- **`docs/outputs_summary.md`:** For a quick, high-level summary of all final project deliverables.

## 🧱 Project Architecture

This project systematically transforms legacy archaeological databases into a modern, integrated geospatial data infrastructure through an eight-phase pipeline. The data flows from legacy database analysis (Phase 1), through ETL (Phase 2), GIS digitization (Phase 3), georeferencing (Phase 4), integration (Phase 5), archival packaging (Phase 6), PostGIS deployment (Phase 7), to final dissemination via APIs and dashboards (Phase 8).

Key architectural decisions include the use of a custom NTv2 transformation to precisely handle the non-standard local coordinate system ("Millon Space") and the strategic choice to use a denormalized schema for the final database to optimize for analytical performance.

[View detailed architecture](docs/architecture.md)

## 📊 Data Sources

### Legacy TMP Databases
- **TMP_DF8, TMP_DF9, TMP_DF10**: Sequential versions of the main TMP database containing survey metadata, surface observations, artifact counts, and archaeological interpretations for 5,046 collection units.
- **TMP_REAN_DF2**: Ceramic reanalysis database with detailed re-tabulation of ceramic collections using updated typologies.

### Spatial Data
- **Raster Basemaps**: Scanned 1:2,000-scale TMP survey raster map tiles of the TMP topographic survey and architectural reconstruction overlay maps from Millon (1973)
- **Legacy Vector Data**: Robertson's digitized collection unit boundaries (MF2) and Sherfield's architectural polygons.
- **Ground Control Points**: High-density GCP dataset for georeferencing from "Millon Space" to global coordinate systems.

[Full data source details](docs/architecture.md#31-data-sources-and-genealogy)

## 🧑‍💻 Quick Start: Setup and Installation

Follow these steps to set up the complete development environment on your local machine.

### Prerequisites

Ensure you have the following software installed and accessible from your command line:

- [Git](https://git-scm.com/)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [Conda](https://docs.conda.io/en/latest/miniconda.html) (Miniconda is recommended)

### Step 1: Clone the Repository

Clone this repository to your local machine using the following command:

```bash
git clone https://github.com/rcesaret/TeoMappingProject.git
cd TeoMappingProject
```

### Step 2: Create and Activate the Conda Environment

This project uses a specific set of Python and system libraries managed by Conda. Create the environment from the provided file:

```bash
conda env create -f envs/digital_tmp_base_env.yml
```

This command will create a new Conda environment named `digital_tmp_base` with all the necessary dependencies. Once the installation is complete, activate the environment:

```bash
conda activate digital_tmp_base
```

### Step 3: Initialize the PostgreSQL Database

The project uses a containerized PostgreSQL/PostGIS database managed by Docker.

1.  **Start the Database Service:** Navigate to the `infrastructure/db/` directory and use Docker Compose to start the database container in detached mode.

    ```bash
    cd infrastructure/db/
    docker-compose up -d
    ```

    This will download the PostGIS image if necessary and start the database server in the background.

2.  **Populate the Databases:** Run the provided Python script to create the necessary databases and load the legacy data from the SQL dumps. From the project's root directory, execute:

    ```bash
    python phases/01_LegacyDB/src/00_setup_databases.py
    ```

    This script will connect to the running Docker container and execute the necessary SQL to set up the project's foundational data.

Your development environment is now fully configured.

## 🛠 Technology Stack Summary

This project leverages a powerful, open-source technology stack.

### Core Infrastructure
- **Database**: PostgreSQL 17 + PostGIS 3.4
- **Programming**: Python 3.11+ (GeoPandas, Shapely, SQLAlchemy, FastAPI) and R (sf, tidyverse, ggplot2, tmap)
- **GIS Desktop**: QGIS 3.40.5
- **Containerization**: Docker ensures consistent and reproducible development and deployment environments.
- **AI-Assisted Development:** Windsurf IDE with MCP Servers

### Specialized Tools by Phase
- **Database Analysis**: SQLAlchemy, psycopg2, Pandas, Graphviz (ERD generation)
- **ETL & Validation**: Great Expectations
- **Georeferencing**: GDAL 3.8+, PROJ 9.0+, custom NTv2 grid tools
- **Web Services**: FastAPI, Leaflet.js for interactive dashboards

For a complete, categorized list of technologies and the rationale for their selection, please see `docs/technical_specs.md`.

## 📈 Key Outputs

### Integrated Database Products
- **TMP_DF12 & TMP_REANs_DF4**: Final analysis-ready datasets with standardized vocabularies and comprehensive metadata.
- **PostGIS Database**: Production-grade spatial database with Docker deployment and API endpoints.
- **Spatial Vector Datasets**: Complete digitization of archaeological, environmental, and modern features with high-precision georeferencing.

### Archival and Distribution
- **tDAR-Compliant Packages**: Archival-ready datasets with comprehensive metadata meeting long-term preservation standards.
- **Multi-Format Exports**: GeoJSON, CSV, Shapefile, and GeoTIFF formats for diverse user needs.

### Public Engagement Tools
- **Interactive WebGIS Dashboard**: Public-facing visualization platform with spatial filtering and data download capabilities.
- **RESTful API Services**: Programmatic access to curated datasets with automated documentation.
- **Comprehensive Tutorial Suite**: Python, R, and QGIS tutorials supporting database setup and spatial analysis workflows.

## 📂 Repository Structure

```
.
├── README.md
├── .env.example
├── .gitignore
├── LICENSE
├───docs/
│   ├── overview.md
│   ├── architecture.md
│   ├── data_sources.md
│   ├── methods.md
│   └── outputs_summary.md
├── envs/
├───data/
│   ├── raw/
│   ├── external/
│   ├── interim/
│   ├── processed/
│   └── final/
├── phases/
│   ├── 01_LegacyDB/
│   │   ├── src/
│   │   ├── notebooks/
│   │   ├── outputs/
│   │   ├── drafts/
│   │   ├── README.md
│   │   └── metadata.json
│   ├── 02_TransformDB
│   │   ├── src/
│   │   ├── notebooks/
│   │   ├── outputs/
│   │   ├── drafts/
│   │   ├── README.md
│   │   └── metadata.json
│   ├── 03_DigitizeGIS
│   │   ├── src/
│   │   ├── notebooks/
│   │   ├── outputs/
│   │   ├── drafts/
│   │   ├── README.md
│   │   └── metadata.json
│   ├── 04_Georef
│   │   ├── src/
│   │   ├── notebooks/
│   │   ├── outputs/
│   │   ├── drafts/
│   │   ├── README.md
│   │   └── metadata.json
│   ├── 05_GeoIntegration
│   │   ├── src/
│   │   ├── notebooks/
│   │   ├── outputs/
│   │   ├── drafts/
│   │   ├── README.md
│   │   └── metadata.json
│   ├── 06_tDAR
│   │   ├── src/
│   │   ├── notebooks/
│   │   ├── outputs/
│   │   ├── drafts/
│   │   ├── README.md
│   │   └── metadata.json
│   ├── 07_PostGIS
│   │   ├── src/
│   │   ├── notebooks/
│   │   ├── outputs/
│   │   ├── drafts/
│   │   ├── README.md
│   │   └── metadata.json
│   └── 08_Dashboards
│       ├── src/
│       ├── notebooks/
│       ├── outputs/
│       ├── drafts/
│       ├── README.md
│       └── metadata.json
├── infrastructure/
│   ├── db/
│   │   └── legacy_db_sql_scripts/
│   │       ├── TMP_DF8.sql
│   │       ├── TMP_DF9.sql
│   │       ├── TMP_DF10.sql
│   │       └── TMP_REAN_DF2.sql
│   └── docker/
├── tests/
├── outputs/
│   ├── figures/
│   ├── metadata_sidecars/
│   └── reports/
└── reports/
    ├── drafts/
    ├── appendices/
    └── figures/
```


| Folder | Purpose |
|--------|---------|
| `phases/01_LegacyDB/` | Database analysis tools, PostgreSQL migration scripts, schema profiling |
| `phases/02_TransformDB/` | ETL scripts, data validation, controlled vocabulary development |
| `phases/03_DigitizeGIS/` | QGIS digitization templates, vector layer validation |
| `phases/04_Georef/` | Georeferencing tools, NTv2 grid generation, accuracy assessment |
| `phases/05_GeoIntegration/` | Spatial integration, feature engineering, architectural classification |
| `phases/06_tDAR/` | Archival packaging, metadata preparation, documentation |
| `phases/07_PostGIS/` | Database deployment, API development, Docker configuration |
| `phases/08_Dashboards/` | WebGIS dashboard, tutorial development |
| `docs/` | Project documentation (architecture, methods, data sources, metadata) |
| `data/` | Raw, interim, processed, and external datasets |
| `infrastructure/` | Database schemas, Docker files, cloud download scripts |

## 👤 Author & Attribution

**Rudolf Cesaretti**
PhD Candidate
[ASU Teotihuacan Research Laboratory](https://shesc.asu.edu/centers/teotihuacan-research-laboratory)
- Email: Rudolf.Cesaretti@asu.edu
- Website: [rcesaret.github.io](https://rcesaret.github.io/)
- LinkedIn: [rudolf-cesaretti](https://www.linkedin.com/in/rudolf-cesaretti)
- GitHub: [rcesaret](https://github.com/rcesaret)
- ASU Profile: [Faculty Directory](https://search.asu.edu/profile/2306101)

### Institutional Affiliations
- **ASU Teotihuacan Research Laboratory**: Primary project host and data repository.
- **Digital Antiquity/tDAR**: Formal archival partner for long-term preservation.

### Citation
Please cite this project as:
> Cesaretti, Rudolf. (2025). Digital TMP: Open Geospatial Integration of the Teotihuacan Mapping Project Data Files. ASU Teotihuacan Research Laboratory. DOI: [to be assigned]

## License

This project is licensed under the MIT License. See the `LICENSE` file for details. Original TMP data remains subject to ASU Teotihuacan Research Laboratory stewardship policies.

---
