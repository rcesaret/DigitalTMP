# 🌐 Digital TMP: Open Geospatial Integration of the Teotihuacan Mapping Project Data Files

> **Purpose:** A comprehensive modernization and digital integration initiative transforming the Teotihuacan Mapping Project’s legacy archaeological datasets into a unified, reproducible, and open-access geospatial research infrastructure, supporting both technical and non-technical audiences.

---

## 📌 Overview

This project modernizes and unifies the legacy datasets of the **Teotihuacan Mapping Project (TMP)**, originally led by René Millon in the 1960s. The TMP represents the only full-surface archaeological survey ever conducted for the ancient city of Teotihuacan, encompassing over 5,000 surface collection units across approximately 37.5 square kilometers. Despite its legacy as the empirical foundation of decades of Mesoamerican research, the TMP dataset remains fragmented across obsolete file formats, incompatible schemas, and spatial systems that prevent integration with modern digital tools.

The Digital TMP Project executes a structured, eight-phase digital transformation pipeline that systematically converts analog archives and legacy software outputs into a unified PostgreSQL/PostGIS platform. The outcome is a modular, reproducible, and open-access geospatial database supporting SQL-based queries, modern GIS formats, and spatial analyses across artifact, architectural, and typological datasets.

---

## 🎯 Objectives

- **Integrate Legacy Datasets**: Merge disparate TMP databases (DF8, DF9, DF10, REANS2) into a unified spatial database with schema harmonization and entity key alignment.
- **Complete Spatial Digitization**: Digitize and georeference all archaeological, environmental, and modern features from 1:2,000 TMP base maps using high-precision georeferencing workflows.
- **Ensure Data Quality and Validation**: Implement automated data quality frameworks to ensure robust, reliable, and reproducible datasets.
- **Comprehensive Documentation**: Develop structured metadata and detailed documentation to facilitate data interpretation and reuse.
- **Enable Open Access**: Publish the finalized spatial database through tDAR, interactive WebGIS platforms, and comprehensive tutorials for diverse user communities.
- **Support Future Research**: Provide high-quality spatial base layers for excavation planning, comparative urbanism studies, and integration with modern geophysical surveys.
- **Establish Extensible Infrastructure**: Create a scalable platform for integrating future TMP excavations, drone photogrammetry, and INAH archival datasets.
- **Enhance Digital Scholarship**: Produce curated datasets and reproducible workflows supporting teaching in archaeology, GIS, and digital humanities.

---

## 🧱 Project Architecture

This project systematically transforms legacy archaeological databases into a modern, integrated geospatial data infrastructure through eight methodologically distinct phases:

### Data Foundation (Phases 1-2)
1. **Database Analysis** – Systematic evaluation and profiling of legacy MS Access databases.
2. **Database Transformation** – Comprehensive ETL and feature engineering to produce analysis-ready datasets.

### Spatial Data Creation (Phases 3-4)
3. **GIS Digitization** – Manual digitization of archaeological, environmental, and modern features.
4. **Georeferencing** – High-precision georeferencing using custom NTv2 transformations.

### Integration and Enhancement (Phase 5)
5. **Geospatial Integration** – Integration of tabular and spatial data with advanced feature engineering.

### Preservation and Distribution (Phases 6-8)
6. **tDAR Outputs** – Preparation and packaging of archival-ready datasets for long-term preservation.
7. **PostGIS Database** – Design and deployment of production-grade spatial database.
8. **Tutorials & Dashboards** – Development of user-facing applications and comprehensive tutorials.

[View detailed architecture](docs/architecture.md)

---

## 📊 Data Sources

### Legacy TMP Databases
- **TMP_DF8, TMP_DF9, TMP_DF10**: Sequential versions of the main TMP database containing survey metadata, surface observations, artifact counts, and archaeological interpretations for 5,046 collection units.
- **TMP_REAN_DF2**: Ceramic reanalysis database with detailed re-tabulation of ceramic collections using updated typologies.

### Spatial Data
- **Raster Basemaps**: Scanned 1:2,000-scale TMP survey raster map tiles of the TMP topographic survey and architectural reconstruction overlay maps from Millon (1973)
- **Legacy Vector Data**: Robertson's digitized collection unit boundaries (MF2) and Sherfield's architectural polygons.
- **Ground Control Points**: High-density GCP dataset for georeferencing from "Millon Space" to global coordinate systems.

### External Resources
- **Modern Reference Data**: Satellite imagery and aerial photography for georeferencing validation.
- **Metadata and Provenance Records**: Comprehensive documentation and metadata in `docs/metadata.md` ensure transparency and long-term interpretability.

[Full metadata and dictionary](docs/data_sources.md)

---

## 🛠 Tools & Technologies

### Core Infrastructure
- **Database**: PostgreSQL 17 + PostGIS 3.4
- **Programming**: Python 3.11+ (GeoPandas, Shapely, SQLAlchemy, FastAPI) and R (sf, tidyverse, ggplot2, tmap)
- **GIS Desktop**: QGIS 3.40.5
- **Containerization**: Docker ensures consistent and reproducible development and deployment environments.

### Specialized Tools by Phase
- **Database Analysis**: SQLAlchemy, psycopg2, Pandas, Graphviz (ERD generation)
- **ETL & Validation**: Great Expectations, dbt (optional), regex libraries
- **Georeferencing**: GDAL 3.8+, PROJ 9.0+, custom NTv2 grid tools
- **Web Services**: FastAPI, Leaflet.js for interactive dashboards
- **Documentation**: LaTeX/Markdown with Pandoc, 7-Zip for archival packaging

---

## 📈 Key Outputs

### Integrated Database Products
- **TMP_DF12 & TMP_REANs_DF4**: Final analysis-ready datasets with standardized vocabularies and comprehensive metadata.
- **PostGIS Database**: Production-grade spatial database with Docker deployment and API endpoints.
- **Spatial Vector Datasets**: Complete digitization of archaeological, environmental, and modern features with high-precision georeferencing.

### Archival and Distribution
- **tDAR-Compliant Packages**: Archival-ready datasets with comprehensive metadata meeting long-term preservation standards.
- **Multi-Format Exports**: GeoJSON, CSV, Shapefile, and GeoTIFF formats for diverse user needs.
- **External Repository Integration**: High-resolution datasets hosted on Zenodo/Figshare with persistent DOIs.

### Metadata and Documentation
- **Controlled Vocabularies and Variable Glossaries**: Documented in human-readable (PDF) and machine-readable (CSV) formats for interoperability.
- **Data Lineage and Provenance**: Version-controlled logs and structured documentation ensure full reproducibility of data transformations.

### Public Engagement Tools
- **Interactive WebGIS Dashboard**: Public-facing visualization platform with spatial filtering and data download capabilities.
- **RESTful API Services**: Programmatic access to curated datasets with automated documentation.
- **Comprehensive Tutorial Suite**: Python, R, and QGIS tutorials supporting database setup and spatial analysis workflows.

### Research Infrastructure
- **Custom CRS Definitions**: PROJ-compatible transformations between "Millon Space" and global coordinate systems.
- **Extensibility Framework**: Modular architecture supporting integration of future excavations, LiDAR, and geophysical surveys.
- **Reproducible Workflows**: Version-controlled code and Docker containers ensuring long-term sustainability.

---

## 📂 Repository Structure

| Folder | Purpose |
|--------|---------|
| `phases/01_LegacyDB/` | Database analysis tools, PostgreSQL migration scripts, schema profiling |
| `phases/02_TransformDB/` | ETL scripts, data validation, controlled vocabulary development |
| `phases/03_DigitizeGIS/` | QGIS digitization templates, vector layer validation |
| `phases/04_Georef/` | Georeferencing tools, NTv2 grid generation, accuracy assessment |
| `phases/05_GeoDB/` | Spatial integration, feature engineering, architectural classification |
| `phases/06_tDAR/` | Archival packaging, metadata preparation, documentation |
| `phases/07_PostGIS/` | Database deployment, API development, Docker configuration |
| `phases/08_Dashboards/` | WebGIS dashboard, tutorial development |
| `docs/` | Project documentation (architecture, methods, data sources, metadata) |
| `data/` | Raw, interim, processed, and external datasets |
| `infrastructure/` | Database schemas, Docker files, cloud download scripts |
| `outputs/` | Final deliverables, figures, and publication materials |

---

## 🧑‍💻 Getting Started

### Environment Setup
1. **Clone Repository**:
```bash
git clone <repository-url>
```
2. **Python Environment**:
```bash
conda env create -f environment.yml
conda activate digital-tmp
```
3. **Database Setup**:
```bash
# Configure PostgreSQL connection
cp .env.example .env
# Edit .env with your database credentials
```

### Data Download
4. **External Datasets**: Follow instructions in `infrastructure/cloud_downloads.md` to download large raster files and legacy databases.
5. **Validation**: Run checksum validation for all downloaded files.
5b. **Metadata Review**: Consult `docs/metadata.md` to familiarize yourself with the data structures, variable definitions, and controlled vocabularies before conducting analyses.

### Phase Execution
6. **Database Migration**: Execute Phase 1 scripts to migrate legacy databases to PostgreSQL.
7. **Sequential Processing**: Follow phase-by-phase workflows documented in each `phases/*/README.md`.

### Docker Deployment (Phase 7)
```bash
cd phases/07_PostGIS/
docker-compose up -d
```

---

## 👤 Author & Attribution

**Rudolf Cesaretti**  
PhD, ASU Teotihuacan Research Laboratory  
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

---

### Licensing

This project is released under the MIT License. See [LICENSE](LICENSE) for details. Original TMP data remains subject to ASU Teotihuacan Research Laboratory stewardship policies.

---
