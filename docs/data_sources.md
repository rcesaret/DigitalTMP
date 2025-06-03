# 📊 Data Sources

> **Purpose**: Comprehensive documentation of all legacy TMP datasets, their provenance, content, and integration pathways into the modern geospatial infrastructure.

---

## 📌 Overview

The Digital TMP project integrates multiple generations of archaeological datasets spanning over five decades of data collection, analysis, and reanalysis. These datasets represent one of the most comprehensive urban-scale archaeological surveys ever conducted, encompassing over 5,000 surface collection units across approximately 37.5 square kilometers of the ancient city of Teotihuacan. The project prioritizes data quality, rigorous metadata, and reproducibility in its integration efforts.

---

## 🗃 Primary Dataset Index

### Legacy TMP Databases

| Dataset | Source | Format | Size | Time Span | Use Case |
|---------|--------|--------|------|-----------|----------|
| **TMP_DF8** | ASU Teo Lab | SQL dump (.sql) | ~15 MB | 1975-1977 | First stable electronic representation, 5,050 cases, 291 variables |
| **TMP_DF9** | ASU Teo Lab (Ian Robertson & Angela Huster) | SQL dump (.sql) | ~18 MB | 1990s | Relational database version with GIS integration capabilities |
| **TMP_DF10** | ASU Teo Lab (Anne Sherfield) | SQL dump (.sql) | ~20 MB | 2022-present | Most recent database with structural improvements and issue documentation |
| **TMP_REAN_DF2** | ASU Teo Lab (Ian Robertson & Angela Huster) | SQL dump (.sql) | ~12 MB | 1973-1983 | Ceramic reanalysis with enhanced typological detail |

### Spatial Data Sources

| Dataset | Source | Format | Size | Coverage | Use Case |
|---------|--------|--------|------|----------|----------|
| **TMP Survey Maps** | René Millon (1962) | Scanned TIFF | ~2 GB | 37.5 km² | 1:2,000 scale photogrammetric base maps |
| **Architectural Overlays** | Various researchers | Scanned TIFF | ~800 MB | Urban core | Red-ink architectural interpretation drawings |
| **Collection Unit Polygons (MF2)** | Ian Robertson | Shapefile | ~50 MB | Survey area | Digitized collection tract boundaries in "Millon Space" |
| **Architectural Polygons** | Anne Sherfield | Shapefile | ~30 MB | Urban core | Digitized architectural features with classification |
| **Modern Satellite Imagery** | Various providers | GeoTIFF | ~1 GB | Regional | Reference data for georeferencing validation |

### Ground Control Points & Reference Data

| Dataset | Source | Format | Size | Purpose | Use Case |
|---------|--------|--------|------|---------|----------|
| **High-Density GCP Dataset** | Manual collection | Shapefile/CSV | ~5 MB | Georeferencing | Control points for "Millon Space" to global CRS transformation |
| **Satellite Images & Aerial Photography** | Various agencies | TIFF/JPEG | ~500 MB | Reference | Modern reference for GCP validation and accuracy assessment |
| **Topographic Maps** | INEGI | PDF/TIFF | ~200 MB | Regional context | Mexican national topographic coverage for validation |

---

## 🏛️ Data Provenance & Institutional Context

### ASU Teotihuacan Research Laboratory
- **Primary Repository**: Houses original TMP datasets and ongoing research.
- **Data Stewardship**: Maintains physical and digital archives.
- **Access**: Institutional repository with controlled access protocols.

### Digital Antiquity/tDAR Partnership
- **Archival Partner**: Long-term preservation and public dissemination.
- **Standards Compliance**: Ensures metadata and format standards.
- **Persistent Identifiers**: DOI assignment for citation and discovery.

### External Data Sources
- **INEGI**: Mexican national geographic institute for topographic reference.
- **Satellite Providers**: Commercial and open-source imagery for validation.
- **Academic Archives**: University at Buffalo and other institutional repositories.

---

## 🧾 Licensing & Permissions

### Research Data
- **TMP Datasets**: Academic use permitted under ASU Teotihuacan Research Laboratory stewardship.
- **Attribution Required**: All use must cite original TMP investigators and current Digital TMP project.
- **Derivative Works**: Permitted for research and educational purposes with proper attribution.

### Reference Data
- **Public Domain**: INEGI topographic maps, US government satellite imagery.
- **Commercial Licensing**: Some high-resolution satellite imagery subject to provider terms.
- **Creative Commons**: Project outputs released under CC-BY for maximum reusability.

### Restrictions
- **Commercial Use**: Some datasets restricted to non-commercial academic research.
- **Cultural Sensitivity**: Data represents Indigenous cultural heritage; respectful use required.
- **INAH Coordination**: Mexican national heritage regulations apply to all cultural materials.

---

## ⚠️ Known Data Quality Issues

### Legacy Database Issues
- **Encoding Inconsistencies**: Variable field lengths restricted by early computing limitations.
- **Missing Records**: ~300 REANs records cannot be matched to main TMP datasets.
- **"Total Counts Problem"**: Subdivision sums occasionally exceed category totals in some variables.
- **Transcription Errors**: Manual data entry from 1960s-1970s field records contains occasional errors.

### Spatial Data Challenges
- **Coordinate System**: Original "Millon Space" requires custom transformation to global CRS.
- **Digitization Variation**: Multiple digitization efforts by different researchers with varying precision.
- **Topology Issues**: Some polygon overlaps and gaps require correction.
- **Scale Limitations**: 1:2,000 base maps limit precision of small-scale features.

### Temporal Inconsistencies
- **Multi-Decade Span**: Data collection and analysis span 1962-2025 with evolving methodologies.
- **Ceramic Reclassification**: REANs reanalysis uses updated typologies not directly comparable to original classifications.
- **Technology Evolution**: Multiple database platforms and GIS software versions.

---

## 🗃 Data Dictionary & Schema Documentation

### Database Documentation
- **[TMP Database Schema Evolution](../docs/database_schema_evolution.md)**: Detailed comparison of DF8, DF9, DF10 structures.
- **[REANs Database Structure](../docs/reans_database_structure.md)**: Ceramic reanalysis schema and variable definitions.
- **[Controlled Vocabularies](../data/processed/controlled_vocabularies/)**: Standardized terminology for all categorical variables.

### Spatial Data Documentation
- **[Digitization Standards](../docs/digitization_standards.md)**: Protocols for manual feature digitization.
- **[Coordinate Reference Systems](../docs/CRS_Catalogue.csv)**: Complete catalog of all CRS used including custom "Millon Space" definitions.
- **[Georeferencing Methodology](../docs/georeferencing_methodology.md)**: Ground control point collection and transformation procedures.

### Metadata Standards
- **[ISO 19115 Compliance](../docs/spatial_metadata_standards.md)**: Spatial metadata implementation.
- **[tDAR Metadata Schema](../docs/tdar_metadata_schema.md)**: Archival metadata requirements and implementation.
- **[Dublin Core Mapping](../docs/dublin_core_mapping.md)**: Standard metadata crosswalk for interoperability.

---

## 📈 Data Integration Pathways

### Phase 1-2: Database Integration
- **Input**: Legacy MS Access databases → **Output**: PostgreSQL with unified schema.
- **Key Transformation**: Denormalization into wide-format analytical tables.
- **Quality Assurance**: Automated validation using Great Expectations framework.

### Phase 3-4: Spatial Data Creation
- **Input**: Raster basemaps → **Output**: Georeferenced vector datasets.
- **Key Transformation**: Manual digitization + high-precision georeferencing.
- **Quality Assurance**: Topology validation and accuracy assessment.

### Phase 5: Geospatial Integration
- **Input**: Transformed databases + georeferenced vectors → **Output**: Unified spatial database.
- **Key Transformation**: Spatial joins and feature engineering.
- **Quality Assurance**: Cross-validation between tabular and spatial data.

---

This comprehensive data foundation supports the full 8-phase transformation pipeline, ensuring that all legacy TMP materials are preserved, integrated, and made accessible for future archaeological research and public engagement.
