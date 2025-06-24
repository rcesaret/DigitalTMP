# Digital TMP - Technical Specifications (Draft v1.0 -- 6/24/2025)

---
**Author:** Rudolf Cesaretti
**Affiliation:** ASU Teotihuacan Research Laboratory
**Date:** June 24, 2025
**Version:** v1.0
---

## **1. Introduction and Project Mandate**

### **1.1 Project Overview**

*   **Project Name:** Digital TMP: Open Geospatial Integration of the Teotihuacan Mapping Project Data Files
*   **Document Version:** 2.0 (Note: This document is a synthesis; source documents have their own versioning, e.g., `overview.md v2.1`, `architecture.md v1.3`).
*   **Author(s):** Rudolf Cesaretti, ASU Teotihuacan Research Laboratory

### **1.2 Purpose and Scope**

This document provides the detailed and definitive technical specifications for the Digital TMP Data Integration Initiative. It outlines the development environment, technology stack, key architectural decisions, design patterns, and data handling protocols that govern the project. Its purpose is to serve as a comprehensive technical guide for the sole developer and as a transparent, reproducible record of the methodologies employed.

This specification builds upon the high-level goals of the project by detailing the specific "how" of implementation, ensuring that all work adheres to the highest standards of reproducibility, scalability, and scholarly rigor. It represents a revised and verified synthesis, building upon prior drafts by injecting critical historical context from the project's technical reports, adding a new section on Design Patterns, and replacing placeholder flags with sourced, verified content. The result is a document with significantly greater technical depth and strategic justification, intended to guide the project through its entire lifecycle, from data remediation to public dissemination.

## **2. Project Goals and Scholarly Aims**

The project is guided by a dual mandate, encompassing both rigorous technical objectives and broader scholarly ambitions.

### **2.1 Core Technical Objectives**

The project is driven by a set of core technical objectives designed to create a robust, reliable, and reproducible data infrastructure that rectifies decades of accumulated data debt.

*   **Database Finalization and Integration:** Systematically audit, clean, and validate the main TMP attribute database (DF10) and the REANS ceramic database. This involves resolving all data ambiguities, rectifying structural inconsistencies, and achieving seamless integration into a structurally optimized final schema (DF12).
*   **Geospatial Data Remediation and Validation:** Complete and validate the georeferencing of all core TMP map products, including the primary architectural map and all 147 "interpretation" sheets, to a high, documented standard of spatial accuracy. This includes performing rigorous spatial cleaning to correct geometric and topological errors (e.g., overlaps, gaps, self-intersections).
*   **Robust Data Integration and Interoperability:** Establish and verify seamless, accurate, and bidirectional linkage between the finalized attribute databases and all cleaned geospatial layers. This linkage will be guaranteed by the consistent and reliable use of unique identifiers (SSN) to ensure absolute relational integrity.
*   **Comprehensive Metadata Development:** Create standardized, machine-readable metadata for all data components. This metadata will cover provenance, methodology, data structure, variable definitions, and georeferencing parameters to ensure long-term usability and adherence to FAIR (Findable, Accessible, Interoperable, Reusable) principles for archival in the tDAR digital repository.
*   **Guaranteed Reproducibility:** Ensure all data transformations, from initial cleaning to final integration, are documented in version-controlled code. Furthermore, all computational environments will be containerized (e.g., via Docker) to guarantee that all processes are fully and precisely reproducible by future researchers on any platform.
*   **Transparent Provenance Tracking:** Maintain a complete and transparent lineage for all data, meticulously documenting every transformation step from the original paper field records and punch cards to the final integrated digital outputs.
*   **Automated Quality Assurance:** Implement a multi-stage validation framework using both automated tools (e.g., Great Expectations) and expert review to enforce data accuracy, consistency, and integrity at every phase of the data pipeline.
*   **Scalability and Extensibility:** Design a modular architecture capable of handling the full complexity and volume of the current TMP dataset while explicitly supporting the future integration of new datasets (e.g., LiDAR, GPR, excavation data) and accommodating inevitable technological evolution.

### **2.2 Scholarly and Project Aims**

Beyond the technical implementation, the project serves a broader set of scholarly, preservationist, and educational goals that define its ultimate success.

*   **Long-Term Preservation and Archival:** Formally archive the complete, integrated, and documented TMP dataset in a trusted digital repository (tDAR). This action is critical to ensure its long-term viability and protection against physical degradation, data loss, or technological obsolescence, safeguarding this invaluable cultural heritage resource for posterity.
*   **Enhanced Accessibility and Dissemination:** Provide multiple, diverse pathways for data access to serve a wide range of users. This includes downloadable datasets in standard open formats (e.g., GeoJSON, CSV), a production-grade PostGIS database for advanced querying, and user-friendly web applications for interactive exploration and visualization.
*   **Fostering Reproducibility and Open Science:** Adhere strictly to open science principles by employing transparent methodologies, publishing well-documented workflows, and using version control (Git) to ensure the complete reproducibility of all data transformations and analytical outputs. This commitment is fundamental to the project's scholarly integrity.
*   **Enabling New Research and Pedagogical Applications:** Unlock the dataset for new generations of researchers and innovative analytical approaches, including advanced quantitative methods, spatial modeling, and machine learning. Concurrently, develop curriculum-aligned modules and tutorials to support the use of TMP data in educational settings for archaeology, digital humanities, and GIS, thereby amplifying its impact.

## **3. Development Environment and Tooling**

The project mandates a standardized, reproducible development environment to ensure consistency, eliminate configuration-related errors, and facilitate long-term maintenance.

### **3.1 Environment Management**

The environment is managed via Conda and is defined in the `envs/digital_tmp_base_env.yml` file. This approach ensures that all contributors and automated processes operate with an identical, version-pinned set of tools and libraries.

*   **Environment Name:** `digital_tmp_base`
*   **Operating Systems:** The technology stack is designed from the ground up to be cross-platform. The exclusive use of Python, Docker, QGIS, and PostgreSQL ensures full compatibility across Windows, macOS, and Linux. The Conda environment file explicitly includes packages like `libwinpthread`, indicating specific consideration for Windows environments alongside core Linux and macOS compatibility, thus guaranteeing a "write once, run anywhere" workflow.

### **3.2 Core Languages and Frameworks**

*   **Programming Languages:**
    *   **Python (v3.11.13):** The primary language for all data transformation (ETL), analysis, scripting, and API development. Its rich ecosystem of data science and geospatial libraries is central to the project.
    *   **R (v4.3+):** Utilized for specialized statistical analysis and the creation of publication-quality visualizations, particularly where existing R packages (e.g., the `tidyverse` suite) offer distinct advantages.
    *   **SQL:** Extensively used for database definition (DDL), data manipulation (DML), and the execution of complex spatial queries within the PostgreSQL/PostGIS environment.

*   **Frameworks:**
    *   **FastAPI:** A modern, high-performance Python web framework used for building the project's RESTful API in Phase 8. Chosen for its speed, automatic documentation generation, and ease of use.
    *   **Great Expectations:** A powerful data validation framework used to implement automated data quality assurance and profiling throughout the ETL pipeline, ensuring data integrity at each step.
    *   **Data Science Pipeline:** The overall project architecture is structured as a formal data science pipeline, emphasizing a sequential, modular, and reproducible workflow from data ingestion to final analysis and dissemination.

### **3.3 Key Libraries**

The project relies on a comprehensive set of open-source libraries. The complete, version-pinned list of over 400 packages is specified in the `envs/digital_tmp_base_env.yml` file. The table below highlights the most critical libraries and their roles.

| Library | Version | Primary Use and Justification |
| :--- | :--- | :--- |
| `pandas` | 2.1.4 | The core library for all tabular data manipulation, cleaning, and analysis in Python. |
| `geopandas` | 1.1.0 | The core library for vector-based geospatial data processing and spatial analysis in Python, integrating `pandas` data frames with `shapely` geometries. |
| `sqlalchemy` | 2.0.41 | The primary Python SQL toolkit and Object-Relational Mapper (ORM) for all database interactions, providing a robust and vendor-agnostic interface to PostgreSQL. |
| `psycopg2` | 2.9.10 | A high-performance, production-ready PostgreSQL database adapter for Python, ensuring efficient communication with the backend database. |
| `gdal` | 3.10.3 | The foundational, industry-standard library for reading, writing, and manipulating raster and vector geospatial data formats. It is the engine behind many other tools. |
| `rasterio` | 1.4.3 | A clean, Pythonic interface for raster data processing, used for handling georeferenced map sheets and any future remote sensing data. |
| `shapely` | 2.1.1 | The fundamental Python package for manipulation and analysis of planar geometric objects, used by GeoPandas to perform geometric operations. |
| `pyproj` | 3.7.1 | The Python interface to the PROJ library, essential for all coordinate reference system (CRS) transformations, including the custom NTv2 transformation. |
| `fastapi` | 0.115.12 | The web framework for building the high-performance RESTful API planned for Phase 8, chosen for its speed and automatic OpenAPI documentation. |
| `docker` | 7.1.0 | The Python library for interacting with the Docker Engine, used to programmatically manage containers for development and deployment. |
| `scikit-learn` | 1.7.0 | A comprehensive machine learning library used for advanced statistical validation, classification tasks, and assessing the accuracy of georeferencing models. |
| `jupyterlab` | 4.4.3 | The interactive development environment for creating and sharing notebooks, code, and data, serving as the primary workbench for exploratory analysis and workflow development. |

### **3.4 Development and GIS Tooling**

The project employs a sophisticated suite of development tools to manage its complex, AI-assisted workflow and manual geospatial data tasks.

*   **IDE:** The **Windsurf Editor IDE** is the primary development environment. It is specifically designed to integrate with a suite of Model Context Protocol (MCP) servers to facilitate AI-driven coding, analysis, and automation, accelerating development while maintaining expert oversight.
*   **MCP Servers:** A collection of specialized, containerized services that provide standardized APIs for the AI agent to interact with the project's resources safely and effectively. Key servers include `desktop-commander` (filesystem access), `github` (version control), `postgres-mcp` (database interaction), `sequential-thinking`, and `code-reasoning`.
*   **GIS Desktop:** **QGIS 3.40.5** is the designated desktop GIS tool for all manual GIS tasks. This includes feature digitization (Phase 3), topology validation, and the critical visual quality assurance of all spatial data outputs. Its open-source nature aligns perfectly with the project's principles.
*   **Containerization:** **Docker** and **Docker Compose** are used extensively for creating reproducible deployment environments. This is particularly critical for packaging the PostGIS database and the MCP servers, ensuring that they can be run identically on any machine, which is a cornerstone of the project's reproducibility goals.

## **4. Technology Stack and Rationale**

The project's technology stack is a carefully curated combination of open-source tools designed for robust, scalable, and reproducible geospatial data science. The selection of each component was deliberate, guided by the project's core principles.

### **4.1 Technology Stack by Domain**

*   **Database and Backend Infrastructure:**
    *   **Core:** **PostgreSQL (v17)** with the **PostGIS (v3.4)** extension.
    *   **Rationale:** A powerful, open-source, and enterprise-grade object-relational database system was chosen as the project's data backbone. PostgreSQL's robustness, combined with the PostGIS extension's best-in-class support for spatial data types, functions, and indexing, makes it perfectly suited for the complex, multi-scalar, and relational nature of archaeological data. This pairing allows for sophisticated queries that can integrate attribute, spatial, and temporal components efficiently. Its proven scalability and performance were benchmarked in Phase 1 and deemed sufficient to handle the full scope of the TMP data and future expansions.

*   **Programming and Analysis Frameworks:**
    *   **Core:** **Python (v3.11+)** and **R (v4.3+)**. The Python ecosystem (`GeoPandas`, `SQLAlchemy`, `Pandas`) is used for core ETL, while the R ecosystem (`tidyverse`, `sf`) is used for specialized statistical analysis. Workflows are documented in **Jupyter Notebooks** and **RMarkdown**.
    *   **Rationale:** An open-source-first approach was prioritized to eliminate licensing costs, prevent vendor lock-in, and ensure the project's methods and results remain accessible to the global research community. Python is the lingua franca for data science and ETL, with robust libraries for every required task. R is included for its unparalleled strengths in specialized statistical analysis and publication-quality visualization. This dual-language approach provides the best tool for every job.

*   **Geospatial Processing Environment:**
    *   **Core:** The foundational library for all spatial data I/O and transformation is **GDAL/OGR (v3.6+)**, complemented by **PROJ (v9.0+)**. **QGIS (v3.40.5)** serves as the primary desktop GIS.
    *   **Rationale:** This suite of open-source tools represents the undisputed industry standard for geospatial data processing. GDAL/OGR provides the foundational engine for all raster and vector data I/O and transformation. PROJ provides the underlying power for all coordinate reference system operations. QGIS offers a user-friendly yet powerful desktop environment for the essential manual digitization and quality assurance tasks that cannot be fully automated.

*   **Deployment, Containerization, and Web Services:**
    *   **Core:** **Docker** is the standard for creating reproducible environments, with **Docker Compose** for orchestration. A RESTful API is built with **FastAPI**, and the web map dashboard will be built with **Leaflet.js**.
    *   **Rationale:** Docker containerization is central to the project's reproducibility principle. It allows the entire PostGIS database environment to be packaged and distributed as a single, consistent, and executable unit. For web services, FastAPI was chosen for its high performance, low overhead, and automatic generation of interactive API documentation (via OpenAPI), making it ideal for building efficient and easy-to-use data-serving endpoints.

## **5.0 Architectural Principles and Key Technical Decisions**

The project's architecture is founded on several key technical decisions made to address the unique and profound challenges of the TMP legacy dataset.

### **5.1 8-Phase Modular Architecture**

The project is structured into eight distinct, sequential phases, from legacy data analysis to final dissemination. This is a foundational architectural choice that enforces a systematic and logical workflow. This modularity breaks down an overwhelmingly complex problem into manageable, verifiable parts. It allows for rigorous quality assurance and validation at the end of each stage, ensuring that errors are caught early. This structure also ensures that data provenance is tracked at each step and facilitates collaboration by allowing specialists to focus on specific phases.

### **5.2 Database Denormalization Strategy**

A **"hybrid normalization"** or **selective denormalization** strategy was chosen for the final PostGIS schema (DF12). This decision is a direct response to the historical evolution and practical use-cases of the TMP databases.

*   **Historical Context:** The initial flat-file structure of DF8 was inflexible and prone to error. The subsequent migration to a highly normalized relational structure in DF9, while theoretically sound from a database design perspective, proved deeply inefficient for the large-scale analytical queries common in archaeological research.
*   **Quantitative Justification:** Phase 1 of the current project confirmed this inefficiency through quantitative benchmarking. Complex queries on the DF9 schema required numerous joins, imposing significant performance penalties that hindered exploratory data analysis.
*   **The Strategy:** The final schema strategically denormalizes certain tables to create wider, analysis-ready tables. This improves read performance for complex queries by reducing the number of required joins, accepting controlled data redundancy as a necessary and justified trade-off for analytical power and speed.

### **5.3 Custom NTv2 Grid Transformation for Georeferencing**

The original TMP maps exist in the local, non-standard "Millon Space" coordinate system, which contains significant, complex, and non-uniform distortions. To achieve the highest possible spatial accuracy, a decision was made to develop and use a custom **NTv2 (National Transformation version 2)** grid shift file.

*   **Insufficiency of Standard Methods:** Standard polynomial or affine transformations were tested and found insufficient for modeling the complex distortions present in the historical maps. They could not provide the sub-2-meter accuracy required by the project.
*   **The NTv2 Workflow:** The NTv2 approach creates a continuous transformation surface that provides superior accuracy (<2m RMSE) and preserves the spatial relationships between features with high fidelity. The specific, reproducible workflow is as follows:
    1.  **GCP Acquisition:** Utilize over 1,900 high-quality Ground Control Points (GCPs) as the basis for the transformation model.
    2.  **Interpolation:** Apply a **Thin Plate Spline (TPS)** interpolation using the `scipy.interpolate.RBFInterpolator` function to model the displacement field between "Millon Space" and the target CRS (WGS 84 / UTM zone 14N).
    3.  **Grid Generation:** Generate a regular grid of displacement vectors (latitude and longitude shifts) from the TPS model.
    4.  **Format Export:** Export this grid to the standard NTv2 binary format (`.gsb`), which is widely supported by GIS software via the PROJ library.
    5.  **Accuracy Assessment:** Rigorously assess the transformation's accuracy using multiple metrics: Root Mean Square Error (RMSE) on an independent set of validation points, Moran's I to check for spatial autocorrelation of residuals (ensuring errors are random and not systematic), and visual analysis of error heatmaps to identify any remaining spatial patterns of distortion.

### **5.4 AI-Assisted Development with MCP Servers**

A strategic decision was made to leverage an AI-driven development model using the Windsurf IDE and a suite of Model Context Protocol (MCP) servers. This is not an attempt to replace the human expert but to augment their capabilities. This model allows for the automation of repetitive coding tasks (e.g., writing boilerplate code, generating unit tests), the systematic enforcement of coding standards and best practices, and the rapid prototyping of complex data transformations. Crucially, a human expert remains "in the loop" for all verification, validation, and final approval. This approach is designed to accelerate development velocity while maintaining, and even enhancing, standards of quality and documentation.

## **6. Design Patterns**

The project's software architecture is guided by established high-level architectural patterns and will adopt specific code-level patterns to ensure a maintainable, testable, and scalable codebase.

### **6.1 High-Level Architectural Patterns**

*   **Data Science Pipeline:** The entire 8-phase project is a macro-level implementation of a data science pipeline pattern. This pattern is characterized by a sequence of distinct processing stages, where the validated output of one stage becomes the input for the next. In this project, the stages are: Legacy Data Analysis → ETL → GIS Digitization → Georeferencing → Geospatial Integration → Archival Packaging → Database Deployment → Dissemination. This ensures a logical flow, modularity, and clear checkpoints for quality assurance between stages.
*   **Staged ETL (Extract, Transform, Load) Pipeline:** Phase 2 (Database Transformation) is a micro-level implementation of a staged ETL pattern. Data is not moved and transformed in a single, monolithic step. It is first **extracted** and consolidated into a provisional dataset. It is then passed to a second **transformation** stage for cleaning, normalization, and feature engineering. Finally, it is **loaded** into the target schema. This staged approach allows for better validation, more precise debugging, and clearer documentation of the complex transformation logic.

### **6.2 Code-Level Design Patterns**

*   **Repository Pattern:** This pattern will be implemented to abstract all data persistence logic. A `PostGisRepository` class will encapsulate all SQL queries and interactions with the PostgreSQL database, likely using SQLAlchemy as its engine. All other application code (e.g., ETL scripts, FastAPI endpoints) will interact with the database *only* through the well-defined methods of this repository. This decouples the application logic from the data store, centralizes data access logic, and dramatically improves the testability of the codebase by allowing the repository to be mocked during unit tests.

    ```python
    # Conceptual example for the technical specification
    class PostGisRepository:
        """
        A repository to handle all interactions with the PostGIS database,
        abstracting SQL and connection management from the application logic.
        """
        def __init__(self, connection_params: dict):
            # ... initialize SQLAlchemy engine and session factory ...
            pass

        def get_collection_unit_by_ssn(self, ssn: int) -> dict:
            # ... logic to query the database for a specific SSN ...
            # Returns a dictionary or a data object.
            pass

        def get_features_in_polygon(self, polygon_wkt: str) -> list:
            # ... logic for a PostGIS ST_Intersects query ...
            # Returns a list of feature objects.
            pass

        def save_cleaned_data(self, data: list):
            # ... logic to bulk insert or update records ...
            pass
    ```

*   **Strategy Pattern:** This pattern will be used in Phase 2 to manage the varied and complex data transformation rules required to clean the legacy datasets. A generic `TransformationContext` will apply different `TransformationStrategy` classes based on the data field or table being processed. For example, there might be a `CeramicTypologyStrategy`, a `SiteDesignationNormalizationStrategy`, or a `FixTotalCountsStrategy`. This approach makes the ETL logic more modular, extensible, and easier to test, adhering to the Open/Closed Principle (open for extension, closed for modification).

## **7. Data Storage, Schema, and Distribution**

The project employs a multi-tiered data storage strategy that distinguishes between the primary analytical database and the various formats used for distribution and archival.

### **7.1 Primary Storage System**

*   **System:** The single source of truth for all integrated data is a **PostgreSQL (v17) database with the PostGIS (v3.4) extension**.
*   **Schema Strategy:** As detailed in Section 5.2, the database schema employs a **Hybrid Normalization Strategy**. Data is selectively denormalized to optimize for complex analytical queries, improving read performance over the highly normalized legacy schemas (like DF9).
*   **Indexing Strategy:** To ensure high performance, the database will be heavily and strategically indexed:
    *   **Spatial Indexing:** **GIST (Generalized Search Tree)** indexes will be created on all geometry and geography columns. These indexes are essential for accelerating spatial queries (e.g., intersects, within, contains) by efficiently partitioning 2D space.
    *   **Attribute Indexing:** A combination of standard **B-Tree** indexes (for primary keys, foreign keys, and other high-cardinality columns used in joins and WHERE clauses) and **BRIN (Block Range Indexes)** will be used. BRIN indexes are particularly effective for very large tables where columns have a natural correlation with their physical storage order (e.g., date/time stamps or sequential IDs), offering significant space savings over B-Tree indexes.

### **7.2 Distribution and Export Formats**

For public distribution and long-term archival in tDAR, the final, validated data is packaged and exported into several standard, open formats to ensure maximum accessibility and interoperability.

*   **Docker Image:** A complete, containerized version of the final PostGIS database, allowing any researcher to spin up an identical copy of the entire database environment with a single command.
*   **SQL Database Dumps:**
    *   `digital_tmp_full_data.sql`: A full dump containing both the schema and all data.
    *   `digital_tmp_schema_only.sql`: A schema-only dump for users who wish to create the database structure without data.
*   **GeoJSON:** The primary format for serving vector data via the RESTful API and for use in web mapping applications (e.g., Leaflet.js).
*   **Shapefile:** Provided for backward compatibility with legacy desktop GIS workflows, though users will be encouraged to use more modern formats like GeoPackage or direct database connections.
*   **CSV (Comma-Separated Values):** For all non-spatial tabular data, ensuring easy use in spreadsheets and statistical software like R or Python with Pandas.
*   **GeoTIFF:** The standard format for all raster datasets, such as the georeferenced historical map sheets.

## **8. API Specifications**

The project includes two distinct categories of APIs: a public-facing RESTful API for data dissemination and a suite of internal APIs used for AI-assisted development.

### **8.1 Public RESTful API**

A RESTful API will be provided in Phase 8 to enable programmatic access to the project's key datasets. The API will be built using FastAPI and will serve data in common web-friendly formats.

| Endpoint | Purpose | Format | Example Query | Rate Limits |
| :--- | :--- | :--- | :--- | :--- |
| `/collections` | Provides access to collection unit geometries and their primary attributes. | GeoJSON | `/collections?bbox=-98.85,19.69,-98.84,19.70` | 1000/hour |
| `/architecture` | Provides access to architectural features with their final classifications. | GeoJSON | `/architecture/{feature_id}` | 1000/hour |
| `/ceramics` | Provides access to ceramic data linked to spatial collection units. | JSON | `/ceramics?ssn=12345` | 1000/hour |
| `/metadata` | Provides access to dataset metadata and controlled vocabularies. | JSON | `/metadata/ceramic_types` | Unlimited |

**Note on API Standards and Future Development:** A full OpenAPI (Swagger) specification will be automatically generated by FastAPI and will serve as the definitive, interactive documentation for the API. It is a strong recommendation that the API design adhere to the **OGC API - Features** standard where possible. This will ensure maximum interoperability with modern desktop and web-based GIS clients, which are increasingly adopting this standard over older protocols like WFS.

### **8.2 Internal Development APIs (MCP Servers)**

The project's development workflow leverages the Windsurf IDE, which interacts with a suite of internal, containerized APIs known as Model Context Protocol (MCP) servers. These are **not for public consumption** but are critical development tools that allow an AI agent to safely and systematically interact with the project's resources under expert supervision. They provide a secure and auditable bridge between the AI and the local development environment.

## **9. Technical Constraints and Legacy Challenges**

The project's design and execution are profoundly shaped by significant technical constraints inherited from the half-century-long, complex history of the Teotihuacan Mapping Project. Acknowledging these constraints is critical for understanding the rationale behind many of the project's technical decisions.

### **9.1 Legacy Data Constraints**

*   **Data Fragmentation:** The core data is split across multiple, non-interoperable database versions (`TMP_DF8`, `DF9`, `DF10`, `TMP_REAN_DF2`), each with different schemas, data types, and naming conventions. A primary task is to reconcile these into a single, coherent whole.
*   **The "Merging" Problem:** The creation of the DF8 database involved a poorly documented "merging" of approximately 5,500 original collection tracts into roughly 5,046 analytical "cases." This created a fundamental and persistent provenience unit mismatch with the collection-based REANS ceramic database, a problem that must be carefully unraveled and resolved.
*   **Pervasive Data Quality Issues:** The datasets contain known and systemic quality problems that must be addressed:
    *   **The "Total Counts Problem":** A pervasive issue, likely stemming from REANS data entry procedures, where the sum of artifact subdivisions (e.g., counts of different ceramic types) exceeds the listed total for a given category. This requires a systematic auditing and flagging strategy.
    *   **Undocumented Reanalysis:** A 1982 infusion of new obsidian data into the DF8 database was not flagged, creating an irresolvable ambiguity between analytical strata within the digital file. This represents a permanent data scar that must be documented in the final metadata.
    *   **Transcription and Coding Errors:** A variety of errors were introduced during the multi-stage manual transcription from paper forms to punch cards and subsequent migrations to digital formats.
*   **Unresolved Cases:** Approximately 350 "particularly problematic collections" from the REANS database could not be reconciled by previous projects and were excluded from the main databases. This project will attempt to resolve as many as possible and will document the status of all of them.

### **9.2 Spatial Data Constraints**

*   **Custom Coordinate System:** All original spatial data exists in "Millon Space," a local, non-standard, rotated Cartesian system. This requires the custom, high-precision NTv2 transformation pipeline (see Section 5.3) to integrate it with any modern GIS data.
*   **Variable Digitization Quality:** The spatial data has been digitized multiple times over several decades by different researchers with varying levels of precision and different methodologies. This has led to geometric and positional inconsistencies that require significant correction and harmonization in Phase 3.
*   **Topological Errors:** Legacy vector files contain pervasive topological issues such as polygon overlaps, gaps between adjacent polygons, and self-intersections. These errors must be systematically identified and corrected to ensure the data is analytically valid for operations like spatial joins and area calculations.

### **9.3 Technological Constraints**

*   **Technological Obsolescence:** The data originated on punch cards and mainframes and has been migrated through a series of now-obsolete platforms like Paradox databases and early versions of MS Access. Each migration carried a significant risk of data corruption, truncation, or loss of fidelity, the effects of which must be investigated.
*   **Lack of Comprehensive Metadata:** For decades, much of the data's interpretation has relied on the institutional and personal knowledge of the original researchers. Formal, machine-readable metadata is often incomplete, inconsistent, or entirely missing, requiring extensive archival research and "data archaeology" to reconstruct.

## **10. System Quality Attributes**

This section outlines the non-functional requirements that govern the quality of the final system, including security, performance, and scalability.

### **10.1 Security Considerations**

The project incorporates specific security measures, primarily focused on protecting the development environment and ensuring safe database interaction.

*   **Secrets Management:** Sensitive information such as the `GITHUB_PERSONAL_ACCESS_TOKEN` and database credentials are managed exclusively via secure environment variables and are never hard-coded or committed to version control, following best practices.
*   **Safe Database Access:** The `postgres-mcp` server, used by the AI agent, provides a `restricted` mode to enforce read-only access and set execution time limits on queries, preventing accidental modification or long-running, resource-intensive queries.
*   **Filesystem Access Control:** The `desktop-commander` MCP server can be configured with a `DESKTOP_COMMANDER_ALLOWED_DIRS` environment variable. This creates an explicit allow-list of directories, effectively sandboxing the AI agent's file operations and preventing it from accessing sensitive areas of the filesystem.
*   **Note on Production Security:** The measures above pertain to the development environment. A formal, comprehensive security plan for the public-facing API, web dashboard, and the production database itself (e.g., user authentication, authorization roles, network security, intrusion detection, and DDoS mitigation) is outside the scope of this initial technical specification. It will be developed as a separate, dedicated document prior to the final deployment in Phase 8.

### **10.2 Performance and Optimization**

Performance optimization is a key consideration to ensure the final PostGIS database can handle complex spatial queries efficiently and support interactive web applications. The performance strategy is multi-faceted:

*   **Strategic Indexing:** As detailed in Section 7.1, a comprehensive indexing strategy using GIST, B-Tree, and BRIN indexes is the first line of defense for query performance.
*   **Materialized Views:** For computationally intensive queries that are executed frequently (e.g., calculating artifact densities per collection unit or aggregating data for the web dashboard), materialized views will be created. These views pre-calculate and store the results, transforming an expensive real-time query into a simple `SELECT` from a table, which can be refreshed on a schedule.
*   **Query Optimization:** All queries, especially those used in the public API, will be analyzed using `EXPLAIN ANALYZE` to ensure they are using the optimal execution plan and leveraging indexes correctly.
*   **Connection Pooling:** The production API server will use a connection pool to manage database connections efficiently, reducing the overhead of establishing a new connection for every incoming request.

### **10.3 Scalability and Extensibility**

The project architecture is explicitly designed for both vertical and horizontal scalability and for future extensibility.

*   **Modular Architecture:** The 8-phase pipeline is inherently modular, allowing future expansion by adding new data sources or analytical workflows as new "phases" or sub-modules without disrupting the existing, validated structure.
*   **Database Scalability:** PostgreSQL is renowned for its ability to scale vertically (by adding more CPU/RAM/storage to the server). The containerized nature of the deployment also facilitates horizontal scaling strategies if ever needed in the distant future.
*   **Future Data Integration:** The system is designed with specific future integrations in mind. The robust schema, consistent use of unique IDs, and modular codebase will accommodate:
    *   Linking TMP excavation unit profiles and detailed stratigraphic data.
    *   Integrating modern remote sensing data such as drone photogrammetry, LiDAR point clouds, or GPR survey results as new layers.
    *   Incorporating external datasets from INAH or other regional surveys through well-defined data federation or integration workflows.

## **11. Open Issues and Uncompleted Tasks**

This project inherits several "uncompleted tasks" from previous initiatives that are treated as known open issues to be addressed. Their resolution is a primary goal of this project.

*   **Resolution of Problematic REANS Collections:** Approximately 350 "particularly problematic collections" within the REANS ceramic database remain unresolved and un-integrated. A dedicated sub-task in Phase 2 will be to investigate each of these cases.
*   **Finalized Georeferencing of all 147 Interpretation Sheets:** The georeferencing of the 147 detailed "interpretation" map sheets was initiated in a prior project but was never fully completed or validated across all sheets. Phase 4 is dedicated to completing this task to a uniform, high standard of accuracy.
*   **Complete Linkage of Architectural Map GIS:** The digitized architectural map was previously identified as having "problems that inhibit easy linkage with the database." Phase 5 is designed to resolve these geometric and attribute-based issues to achieve a seamless link.

## **12. Future Considerations**

While the current project scope is focused on creating a foundational, integrated dataset, it is designed as an infrastructure upon which future research can build. Potential future enhancements envisioned include:

*   **Integration of Excavation Data:** A major future project would be to link the detailed profiles, stratigraphic relationships, and artifact data from the numerous TMP excavation units, adding a crucial third dimension (depth/time) to the surface survey data.
*   **Integration of Modern Remote Sensing Data:** Incorporating high-resolution datasets such as drone-based photogrammetry, LiDAR, or geophysical survey overlays to compare with and enrich the historical mapping data.
*   **Temporal and Chronological Modeling:** Adding more explicit temporal annotations and formal chronological relationships to the database, allowing for more sophisticated time-aware queries and analysis of the city's diachronic development.
*   **Development of Advanced Analytical Tools:** Building a suite of specialized analytical tools on top of the API and database, such as network analysis of the street system or machine learning models for predicting site function.

---
