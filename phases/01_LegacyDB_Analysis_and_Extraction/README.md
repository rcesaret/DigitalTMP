# Phase 1: Legacy Database Profiling & Analysis

> **Purpose**: This phase focuses on the systematic evaluation of the legacy Teotihuacan Mapping Project (TMP) databases. The goal is to produce actionable insights into their quality, complexity, and suitability for transformation and integration into a modern relational and geospatial data architecture. The outcomes of this phase directly inform schema redesign decisions, guide denormalization strategies, and establish a reproducible baseline for validating future data transformations.

## 🎯 Objective

To conduct a comprehensive analysis of the legacy TMP databases (DF8, DF9, DF10, and REAN_DF2) by:
*   Creating validated and reproducible PostgreSQL instances of these databases.
*   Performing automated database profiling and structural visualization.
*   Conducting quantitative schema analysis to understand their structure and complexity.
*   Developing a strategic proposal for a unified, denormalized target schema optimized for analytical workflows and geospatial integration.

## 📊 Data Inputs

| File/Dataset          | Description                                                                 | Format                     | Location                                                                 |
| :-------------------- | :-------------------------------------------------------------------------- | :------------------------- | :----------------------------------------------------------------------- |
| TMP_DF8               | Legacy TMP core research database (surface observations, artifact counts)   | MS Access MDB / SQL Dump   | `data/external/` or via `infrastructure/cloud_downloads.md`            |
| TMP_DF9               | Updated version of DF8                                                      | MS Access MDB / SQL Dump   | `data/external/` or via `infrastructure/cloud_downloads.md`            |
| TMP_DF10              | Further updated version of DF9                                                | MS Access MDB / SQL Dump   | `data/external/` or via `infrastructure/cloud_downloads.md`            |
| TMP_REAN_DF2          | Ceramic reanalysis database                                                 | MS Access MDB / SQL Dump   | `data/external/` or via `infrastructure/cloud_downloads.md`            |
| Historical Docs       | Data dictionaries, codebooks, existing schema documentation               | PDF, TXT, DOCX             | `project_materials/` or `docs/references/` (conceptual paths)          |
| Provenance Docs       | Documentation on database history and modifications                       | PDF, TXT, DOCX             | `project_materials/` or `docs/references/` (conceptual paths)          |

## 🔄 Workflows

This phase consists of the following key workflows:

1.  **Workflow 1.1: Legacy Database Instantiation & Validation**
    *   Establishes a reproducible pipeline for creating and populating PostgreSQL versions of the legacy TMP databases (DF8, DF9, DF10, REAN_DF2).
    *   Ensures all subsequent schema evaluations are conducted on validated, consistent database instances.
    *   Leverages automated tooling for database creation, data loading, and initial validation.

2.  **Workflow 1.2: Database Schema Profiling & Quantitative Analysis**
    *   Systematically analyzes the structure, content, and relational integrity of the instantiated PostgreSQL databases.
    *   Utilizes automated profiling tools to generate comprehensive reports on data types, distributions, missing values, and potential quality issues.
    *   Generates visual ERDs and quantitative metrics to document schema complexity.

3.  **Workflow 1.3: Denormalization Strategy & Schema Redesign Proposal**
    *   Synthesizes findings from profiling and analysis to develop a strategic proposal for a unified, denormalized target schema.
    *   Optimizes the proposed schema for analytical workflows, geospatial integration, and long-term maintainability.
    *   Documents the rationale behind redesign decisions in a comprehensive white paper.

##  deliverables Key Outputs & Deliverables

| Output                                                      | Description                                                                                                   | Format             | Location                         |
| :---------------------------------------------------------- | :------------------------------------------------------------------------------------------------------------ | :----------------- | :------------------------------- |
| Validated PostgreSQL Instances                              | Reproducible PostgreSQL versions of DF8, DF9, DF10, and REAN_DF2.                                               | PostgreSQL DB      | Local Docker / Server Instance   |
| Schema Profiling Reports                                    | Comprehensive reports from tools like `Pandas Profiling` detailing data characteristics for each database.    | HTML, JSON         | `phases/01_LegacyDB/outputs/profiling_reports/`    |
| Automated Entity-Relationship Diagrams (ERDs)               | Visual diagrams of database schemas generated using tools like `Graphviz`.                                    | PNG, SVG, DOT      | `phases/01_LegacyDB/outputs/erds/`             |
| Quantitative Schema Metrics                                 | Statistics on table counts, column types, relationship complexities, etc.                                     | CSV, Markdown      | `phases/01_LegacyDB/outputs/schema_metrics/`   |
| Denormalization White Paper & Schema Redesign Proposal      | A detailed document outlining the analysis, rationale, and proposed target schema for subsequent phases.        | PDF, Markdown      | `phases/01_LegacyDB/outputs/reports/`          |

## 🛠 Tools & Technologies

*   **Databases**:
    *   PostgreSQL (latest stable version, e.g., 17)
*   **Programming & Scripting**:
    *   Python (with libraries: Pandas, SQLAlchemy, Psycopg2, pyodbc)
    *   SQL
*   **Database Profiling**:
    *   Pandas Profiling (or similar like DataCleaner, Sweetviz)
*   **Schema Visualization**:
    *   Graphviz
    *   DbVisualizer, pgAdmin ERD Tool (or equivalent)
*   **Development Environment**:
    *   Jupyter Notebooks
*   **Version Control**:
    *   Git

---

For more detailed information on the overall project, see the main [Project README.md](../../README.md) and the [Project Architecture document](../../docs/architecture.md).
