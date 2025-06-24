# Digital TMP - Project Outputs Summary (Draft v2.0 -- 6/24/2025)

---
**Author:** Rudolf Cesaretti
**Affiliation:** ASU Teotihuacan Research Laboratory
**Date:** June 24, 2025
**Version:** v2.0
---

## 1. Executive Summary & Project Context

### 1.1 Purpose and Vision

This document provides a comprehensive and definitive summary of all final outputs, deliverables, and research products generated through the eight-phase Digital Teotihuacan Mapping Project (TMP) Integration Initiative. It is designed to serve as the project's central "results dashboard," showcasing the full scope and impact of the transformation of a landmark legacy archaeological dataset into a modern, accessible, and sustainable research infrastructure.

The outputs detailed herein are architected to serve a wide and diverse range of academic, educational, and public audiences—from advanced researchers conducting complex spatial analyses to students and members of the public exploring this invaluable cultural heritage dataset for the first time. Every product has been developed with the core principles of long-term accessibility, usability, reproducibility, and preservation at its foundation.

This portfolio references and builds upon the project's foundational documentation, and readers are encouraged to consult these for deeper technical context:
- **[README.md](README.md)** and **[overview.md](docs/overview.md)** for detailed, high-level project overviews and mission statement, project context, goals, background, project outline, architecture overview, and general summaries.
- **[architecture.md](docs/architecture.md)** for a comprehensive architectural blueprint of the project, detailing the system's design, structure, components, data flow, analytical methods, modelling choices, statistical procedures, datasets and databases, and integration pathways.
- **[technical_specs.md](docs/technical_specs.md)** for comprehensive documentation of technical specifications, software, implementation details, methods and coding standards.

### 1.2 Recent Enhancements and Status

All outputs have undergone rigorous validation and provenance tracking, ensuring that each product is fully documented, reproducible, and aligned with open science principles. This document reflects the final state of all deliverables, incorporating several key updates to enhance clarity, accuracy, and usability:

- **Standardized Formats:** All database deliverables now consistently reference PostgreSQL dump files (`.sql`) as the primary distribution format, superseding older or intermediate formats.
- **Data Quality Metrics:** The project-wide Data Quality Score has been finalized at **98.5%**, representing the pass rate of all data points against our automated validation and integrity checks.
- **DOI Assignment:** The status of Digital Object Identifier (DOI) assignment for archival packages has been clarified. DOIs are currently pending and are expected to be formally assigned and resolved by the project's conclusion.
- **Educational Focus:** Educational resources now include explicitly stated intended learning outcomes for both student and researcher audiences, clarifying their pedagogical value.
- **API Access:** All documentation for API services now clearly notes authentication requirements, specifying that an API key is required for access to prevent abuse and ensure service stability.

---

## 2. Core Database & Analytical Products

The heart of the Digital TMP initiative is the creation of a unified, validated, and analysis-ready database. These products represent the culmination of the project's intensive data transformation, cleaning, and integration work, primarily conducted in Phase 2 of the project pipeline.

### 2.1 Transformed Archaeological Databases

These two primary tabular datasets represent the core analytical outputs of the project's data synthesis work. They are meticulously cleaned, cross-referenced, and enriched with standardized terminologies, ready for immediate use in statistical and analytical software.

- **`TMP_DF12`:** This is the final, master analysis-ready dataset, representing a complete synthesis of the legacy DF8, DF9, and DF10 databases. It contains the main site, architectural, and artifact attribute data, with all variables harmonized using controlled vocabularies.
- **`TMP_REANs_DF4`:** This dataset contains the fully cleaned, reconciled, and finalized data from the comprehensive ceramic reanalysis project. It features enhanced typological detail and has been rigorously cross-validated against the primary site data.

The specific deliverables for these datasets are detailed below:

| Output | Description | Format | Size | Link |
|--------|-------------|--------|------|------|
| **TMP_DF12** | Final analysis-ready dataset integrating DF8/9/10 with standardized vocabularies. | PostgreSQL dump (.sql)/CSV | ~25 MB | [Database Schema](../phases/02_TransformDB/outputs/TMP_DF12_schema.sql) |
| **TMP_REANs_DF4** | Finalized ceramic reanalysis dataset with enhanced typological detail. | PostgreSQL dump (.sql)/CSV | ~15 MB | [Data Dictionary](../phases/02_TransformDB/outputs/REANs_DF4_dictionary.yaml) |

### 2.2 Controlled Vocabularies & Provenance Logs

To ensure absolute transparency, reproducibility, and scholarly rigor, the project provides a complete suite of documentation that traces every decision made during the data transformation process. These materials are essential for understanding the data's structure and for replicating the project's results.

| Output | Description | Format | Size | Link |
|--------|-------------|--------|------|------|
| **Controlled Vocabularies** | Standardized terminology tables for all categorical variables, serving as the project's official glossary. | CSV/PDF | ~5 MB | [Vocabulary Files](../phases/02_TransformDB/outputs/controlled_vocabularies/) |
| **Variable Transformation Log** | Complete, human- and machine-readable documentation of all data modifications, cleaning steps, and feature engineering. | YAML/PDF | ~2 MB | [Transformation Report](../phases/02_TransformDB/outputs/transformation_log.pdf) |

### 2.3 Legacy Database Analysis Products

As part of the initial project phases, a comprehensive analysis of the legacy database structures was conducted. These reports document the state of the source data and provide the explicit rationale for the schema optimization and denormalization decisions that informed the final database architecture. They are crucial for understanding the "before and after" state of the TMP data.

| Output | Description | Format | Size | Link |
|--------|-------------|--------|------|------|
| **Schema Profiling Reports** | Quantitative and statistical analysis of the legacy database structures, tables, and variable distributions. | HTML/PDF | ~10 MB | [Profiling Dashboard](../phases/01_LegacyDB/outputs/schema_profiling/) |
| **Entity-Relationship Diagrams** | Visual documentation of the original, complex relationships within the legacy databases. | SVG/PDF | ~3 MB | [ERD Gallery](../phases/01_LegacyDB/outputs/database_erds/) |
| **Denormalization White Paper** | A technical report providing performance analysis and detailed recommendations for schema optimization. | PDF | ~5 MB | [Technical Report](../phases/01_LegacyDB/outputs/denormalization_analysis.pdf) |

---

## 3. Geospatial Data Products

This project will produce the most complete, accurate, and professionally documented set of geospatial data for the Teotihuacan Mapping Project ever assembled.

### 3.1 Foundational Georeferencing Standard

A cornerstone of the project's geospatial work is the establishment of a single, authoritative coordinate reference system (CRS). All final spatial data products have been meticulously georeferenced to **UTM Zone 14N (WGS 84), EPSG:32614**. This modern, standard projection ensures interoperability with global datasets and compatibility with all modern GIS software and web mapping platforms.

### 3.2 Digitized Vector Datasets

This is a complete and validated set of vector layers representing all archaeological, environmental, and modern features digitized from the original TMP maps during Phase 3. Each feature has been cleaned, validated, and enriched with attributes from the core databases.

| Layer | Format | Features | Coverage | Description |
|-------|--------|----------|----------|-------------|
| **Archaeological Features** | GeoJSON/Shapefile | ~15,000 | Urban core | Floors, walls, plazas, mounds, excavations, and artifact concentrations. |
| **Environmental Features** | GeoJSON/Shapefile | ~5,000 | Full survey | Terraces, canals, drainage systems, and other water management features. |
| **Modern Features** | GeoJSON/Shapefile | ~8,000 | Full survey | Roads, buildings, modern infrastructure, and contemporary land use polygons. |
| **Collection Unit Boundaries** | GeoJSON/Shapefile | 5,046 | 37.5 km² | The final, validated survey tract polygons that serve as the primary unit of spatial analysis. |
| **Architectural Classifications** | GeoJSON/Shapefile | ~3,500 | Urban core | Hierarchical functional interpretations of structures, classified by type and period. |

### 3.3 Georeferenced Raster Layers

To provide complete contextual and historical data, high-resolution, georeferenced versions of the two foundational TMP maps are provided. These serve as critical base layers for analysis and visualization.

- **TMP Topographic Survey Map:** The complete black-ink base map showing all original survey data, contour lines, and topography.
- **TMP Architectural Reconstruction Map:** The complete red-ink overlay map illustrating René Millon's authoritative architectural interpretations and reconstructions.

Both layers are provided as high-resolution **GeoTIFF (`.tif`)** files, precisely aligned to the project's UTM Zone 14N CRS.

### 3.4 Georeferencing Transformation & Validation Products

A key scientific output of this project is the set of tools and reports that make our high-accuracy georeferencing workflow fully transparent and reproducible. These products document the complex process of transforming the data from its original, non-standard local coordinate system (informally known as "Millon Space") into the standard UTM projection.

| Output | Description | Format | Accuracy | Link |
|--------|-------------|--------|----------|------|
| **Custom NTv2 Grid File** | The high-precision grid shift file containing displacement vectors to transform data from "Millon Space" to UTM. | .gsb | <2m RMSE | [Transformation Grids](../phases/04_Georef/outputs/ntv2_grids/) |
| **Ground Control Points** | The high-density dataset of over 1,900 survey-grade GCPs used for the transformation and its validation. | Shapefile/CSV | Survey-grade | [GCP Database](../phases/04_Georef/outputs/gcp_dataset.geojson) |
| **Accuracy Assessment Report** | A comprehensive report detailing the statistical spatial error analysis, including final RMSE calculations. | PDF | Statistical | [Error Analysis](../phases/04_Georef/outputs/accuracy_assessment.pdf) |
| **Custom CRS Definitions** | PROJ-compatible definitions for all coordinate systems used, including the legacy "Millon Space." | .prj/.json | Reference | [CRS Catalog](../docs/CRS_Catalogue.csv) |

---

## 4. Production Infrastructure & Integrated Data Environment

Beyond static files, the project delivers a dynamic, high-performance data environment designed for sophisticated analysis and programmatic access.

### 4.1 Unified PostGIS Production Database

The project's capstone data product is a complete, open-source relational database built on **PostgreSQL (v17+)** with the **PostGIS (v3.4+)** spatial extension. This database is not merely a container for disparate files; it is a cohesive analytical environment where all tabular and spatial data are fully integrated. It contains the `TMP_DF12` and `TMP_REANs_DF4` tables, all georeferenced vector layers, and is enhanced with spatial indexes and materialized views to ensure high performance for complex analytical queries.

| Layer | Description | Records | Spatial Coverage | Key Attributes |
|-------|-------------|---------|------------------|----------------|
| **Unified Collection Units** | A spatially-enabled table joining TMP_DF12, REANs_DF4, and collection unit geometries. | 5,046 | Complete survey | Ceramics, architecture, chronology, spatial metrics. |
| **Architectural Typology** | Classified building features with functional interpretations, linked to parent structures. | ~3,500 | Urban core | Type, function, period, spatial relationships. |
| **Derived Spatial Variables** | Pre-calculated, engineered features (e.g., density, proximity, complexity) for each collection unit. | 5,046 | Complete survey | Area, perimeter, shape indices, centroid coordinates. |
| **Cross-Validated Datasets** | The final, quality-assured spatial-attribute integrations with confidence scores and full provenance tracking. | 5,046 | Complete survey | Confidence scores, validation flags, provenance. |

### 4.2 Deployment & Access Infrastructure

To ensure this powerful database is accessible to a wide range of technical users, it will be distributed in two primary forms.

| Component | Description | Format | Access Method | Link |
|-----------|-------------|--------|---------------|------|
| **Dockerized Database** | A complete, containerized PostgreSQL/PostGIS deployment managed via `docker-compose.yml` for one-command setup. | Docker Image | Container deployment | [Docker Hub](../phases/07_PostGIS/outputs/docker/) |
| **SQL Database Dumps** | Full data (`full_data.sql`) and schema-only (`schema_only.sql`) exports for direct restoration into any PostgreSQL instance. | .sql | Direct restoration | [Database Exports](../phases/07_PostGIS/outputs/sql_dumps/) |
| **Performance Optimization** | A suite of SQL scripts for creating spatial indexes and materialized views to accelerate common queries. | SQL | Database queries | [Optimization Scripts](../phases/07_PostGIS/outputs/optimization/) |

### 4.3 Multi-Format Data Exports

For users who do not require the full database environment, all key datasets are also provided as static exports in multiple standard formats, ensuring maximum compatibility across different software and use cases.

| Format | Purpose | Size | Update Frequency | Download Link |
|--------|---------|------|------------------|---------------|
| **GeoJSON** | Web mapping, data exchange, and JavaScript applications. | ~150 MB | Static release | [GeoJSON Exports](../outputs/geojson/) |
| **Shapefile** | Maximum compatibility with desktop GIS applications (e.g., QGIS, ArcGIS). | ~200 MB | Static release | [Shapefile Package](../outputs/shapefiles/) |
| **CSV** | Use in spreadsheets and any statistical or data analysis software (e.g., R, Python/pandas). | ~50 MB | Static release | [Tabular Data](../outputs/csv/) |
| **GeoTIFF** | The foundational raster maps for analysis and visualization in GIS and remote sensing software. | ~500 MB | Static release | [Raster Products](../outputs/geotiff/) |

---

## 5. Dissemination, Engagement & Educational Resources

To maximize the project's impact, a suite of public-facing tools and educational materials has been developed to lower the barrier to entry for exploring and analyzing this rich dataset.

### 5.1 Public-Facing Interactive Tools

These tools provide powerful ways to interact with the data without requiring specialized software or technical expertise.

#### 5.1.1 WebGIS Dashboard
A public-facing, interactive web map designed for the visual exploration of the integrated TMP dataset. It allows users to overlay data layers, click on features to view attribute information, and perform simple spatial and attribute queries directly in their web browser.

| Feature | Description | Technology | Access | Demo |
|---------|-------------|------------|--------|------|
| **Interactive Map** | Public-facing visualization with layer control and spatial filtering. | Leaflet.js | Web browser | [Live Dashboard](../phases/08_Dashboards/outputs/webgis/) |
| **Data Explorer** | Tools for attribute querying, data filtering, and simple charting. | JavaScript/FastAPI | Web interface | [Explorer Demo](../phases/08_Dashboards/outputs/explorer/) |
| **Download Portal** | A centralized hub for direct access to all static datasets and links to API endpoints. | HTML/CSS | Public access | [Download Center](../phases/08_Dashboards/outputs/downloads/) |
| **Educational Features** | Guided tours, informational popups, and curated views for public engagement. | Interactive JS | Public engagement | [Education Mode](../phases/08_Dashboards/outputs/education/) |

#### 5.1.2 RESTful API Services
A public RESTful API, built with **FastAPI**, provides programmatic access to curated subsets of the final database. This service, which requires an API key for authenticated access, allows researchers and developers to seamlessly integrate Teotihuacan data into their own applications, models, and analytical workflows.

| Endpoint | Purpose | Format | Rate Limits | Documentation |
|----------|---------|--------|-------------|---------------|
| `/collections` | Retrieve collection unit geometries and all associated attributes. | GeoJSON | 1000/hour | [API Docs](../phases/08_Dashboards/outputs/api/collections/) |
| `/architecture` | Query architectural features with their detailed classifications. | GeoJSON | 1000/hour | [API Docs](../phases/08_Dashboards/outputs/api/architecture/) |
| `/ceramics` | Access ceramic data with spatial relationships to collection units. | JSON | 1000/hour | [API Docs](../phases/08_Dashboards/outputs/api/ceramics/) |
| `/metadata` | Fetch dataset metadata, controlled vocabularies, and variable definitions. | JSON | Unlimited | [API Docs](../phases/08_Dashboards/outputs/api/metadata/) |

### 5.2 Comprehensive Tutorial Suite & Educational Materials

A suite of comprehensive, step-by-step tutorials demonstrates how to access, query, and conduct common analytical tasks with the project's data, empowering a new generation of researchers.

| Tutorial | Platform | Skill Level | Duration | Link |
|----------|----------|-------------|----------|------|
| **Python Database Tutorial** | Jupyter Notebooks | Intermediate | 2-3 hours | [Python Guide](../phases/08_Dashboards/outputs/tutorials/python/) |
| **R Spatial Analysis Tutorial** | RMarkdown | Intermediate | 2-3 hours | [R Guide](../phases/08_Dashboards/outputs/tutorials/r/) |
| **QGIS Desktop Tutorial** | PDF with screenshots | Beginner | 1-2 hours | [QGIS Guide](../phases/08_Dashboards/outputs/tutorials/qgis/) |
| **Database Setup Guide** | Multi-format | Technical | 30 minutes | [Setup Instructions](../phases/08_Dashboards/outputs/tutorials/setup/) |

In addition to tutorials, the project delivers a collection of teaching-ready resources.

| Resource | Purpose | Format | Target Audience | Link |
|----------|---------|--------|-----------------|------|
| **Classroom Dataset** | A curated, simplified subset of the data, ideal for coursework and student projects. | Multiple | Educators | [Teaching Materials](../outputs/education/classroom_data/) |
| **Analysis Templates** | Pre-configured scripts and workflows for common analytical tasks (e.g., density mapping, cluster analysis). | Jupyter/R | Researchers | [Template Library](../outputs/education/templates/) |
| **QGIS Project Files** | Ready-to-use project files with all layers loaded, styled, and organized for immediate use. | .qgs | GIS Users | [QGIS Projects](../outputs/education/qgis_projects/) |

---

## 6. Archival, Preservation & Long-Term Sustainability

A primary goal of this project is to ensure the long-term preservation and professional curation of the TMP's invaluable digital legacy, guaranteeing its availability for future generations.

### 6.1 Formal Archival Packages

#### 6.1.1 tDAR-Compliant Submission
A complete, formal archival package has been prepared for ingestion into **tDAR (The Digital Archaeological Record)**, a trusted, CoreTrustSeal-certified digital repository. This package bundles all data products with the comprehensive metadata and documentation required for long-term preservation and independent reuse. The full, final `glossary.md` is included as the project's official data dictionary.

| Package | Description | Format | DOI Status | tDAR Link |
|---------|-------------|--------|------------|-----------|
| **Complete Spatial Database** | The full PostGIS database with comprehensive, multi-level metadata. | Multiple | Pending | [tDAR Submission](../phases/06_tDAR/outputs/tdar_packages/) |
| **Digitized GIS Layers** | All individual vector datasets with their full attribute extensions. | Shapefile/CSV | Pending | [Spatial Package](../phases/06_tDAR/outputs/spatial_package/) |
| **Documentation Suite** | All methodology, tutorials, white papers, and technical reports. | PDF | Pending | [Documentation](../phases/06_tDAR/outputs/documentation/) |
| **Controlled Vocabularies** | The complete set of standardized terminology and glossaries. | CSV/PDF | Pending | [Vocabularies](../phases/06_tDAR/outputs/vocabularies/) |

#### 6.1.2 External Repository Integration
To maximize accessibility and adhere to FAIR data principles, key outputs are also deposited in other major open-access repositories.

| Repository | Content | Size | DOI | Access |
|------------|---------|------|-----|--------|
| **Zenodo** | High-resolution raster datasets (GeoTIFFs) and large data files. | ~2 GB | Pending | [Zenodo Collection](https://zenodo.org/communities/digital-tmp) |
| **Figshare** | Complete database exports (SQL/CSV) and all technical documentation. | ~500 MB | Pending | [Figshare Project](https://figshare.com/projects/digital-tmp) |
| **GitHub** | All source code, ETL scripts, and reproducible computational workflows. | ~100 MB | N/A | [GitHub Repository](https://github.com/rcesaret/digital-tmp) |

### 6.2 Reproducibility & Version Control

Ensuring the project is computationally reproducible is a core deliverable.

| Component | Description | Language/Format | Maintenance | Repository |
|-----------|-------------|-----------------|-------------|------------|
| **ETL Pipelines** | The complete, commented data extraction, transformation, and loading workflows. | Python/SQL | Active | [ETL Scripts](../phases/*/src/) |
| **Validation Frameworks** | The automated quality assurance routines and data integrity tests. | Python/Great Expectations | Active | [Validation Suite](../tests/) |
| **Documentation Source** | All project documentation in its source format for easy updating and regeneration. | Markdown/LaTeX | Active | [Docs Source](../docs/) |
| **Docker Configurations** | The reproducible deployment environments for the database and API. | Docker/YAML | Active | [Infrastructure](../infrastructure/) |

### 6.3 Long-Term Sustainability Plan

A formal plan outlines the procedures for ongoing maintenance and stewardship of the project's digital assets.

| Aspect | Implementation | Timeline | Responsibility |
|--------|----------------|----------|----------------|
| **Version Control** | Git-based tracking of all code and documentation with semantic versioning. | Ongoing | Development Team |
| **Dependency Management** | Conda/pip environment specifications (`environment.yml`) are locked for each release. | Per release | Technical Lead |
| **Documentation Updates** | A scheduled quarterly review and revision cycle to ensure all documentation remains current. | Quarterly | Project Lead |
| **Archive Synchronization** | Annual updates to tDAR and other external repositories to synchronize any data corrections or additions. | Annual | Data Steward |

---

## 7. Summary Metrics & Project Visualizations

To communicate the project's scope and impact effectively, a series of summary dashboards and figures are provided.

### 7.1 Key Metrics Dashboard

| Metric | Value | Description |
|--------|-------|-------------|
| **Collection Units Processed** | 5,046 | Complete coverage of the original TMP survey area. |
| **Digitized Features** | ~28,000 | Total count of archaeological, environmental, and modern features. |
| **Database Variables** | 400+ | The number of standardized and validated attributes in the final database. |
| **Spatial Accuracy** | <2m RMSE | The final root-mean-square error for the georeferencing transformation. |
| **Data Quality Score** | 98.5% | The pass rate of all data against automated validation and integrity checks. |

### 7.2 Project Impact Visualizations

A set of high-quality, presentation-ready figures are available for use in reports and publications.

| Visualization | Description | Format | Link |
|---------------|-------------|--------|------|
| **Transformation Pipeline** | A complete workflow diagram illustrating the data's journey from legacy files to the modern database. | SVG/PNG | [Pipeline Diagram](../outputs/figures/transformation_pipeline.svg) |
| **Spatial Coverage Map** | A cartographic product visualizing the full survey extent and the density of key archaeological features. | PDF/PNG | [Coverage Map](../outputs/figures/spatial_coverage.png) |
| **Data Quality Dashboard** | An interactive HTML report showing detailed validation results, error distributions, and cleaning summaries. | Interactive HTML | [Quality Dashboard](../outputs/figures/quality_dashboard.html) |
| **Temporal Evolution** | A timeline graphic illustrating the database development history, key project milestones, and version releases. | PDF/PNG | [Timeline Graphic](../outputs/figures/temporal_evolution.png) |

---

## 8. Conclusion

This comprehensive output portfolio demonstrates the successful transformation of the Teotihuacan Mapping Project's invaluable legacy data. The result is a modern, integrated, and accessible research ecosystem that is not only fit for 21st-century analytical methods but is also preserved for the long term. By providing a multi-tiered suite of products—from a high-performance database and API for technical experts to an interactive web map and tutorials for students and the public—the Digital TMP project establishes a new standard for the stewardship and dissemination of archaeological data, ensuring this irreplaceable cultural heritage dataset can continue to fuel discovery for decades to come.

---
