# 🧠 Methods & Analytical Approach

> **Purpose:** Comprehensive documentation of the methodological framework, analytical techniques, and technical workflows employed across all eight phases of the Digital TMP project.

## 📊 Overall Methodological Framework

The Digital TMP project employs a **data science pipeline approach** that systematically transforms legacy archaeological databases into a modern, integrated geospatial data infrastructure. The methodology is structured around eight sequential phases, each with specialized analytical techniques designed to address specific challenges of archaeological data modernization, spatial integration, and long-term preservation.

### Core Methodological Principles
- **Reproducibility**: All transformations documented in version-controlled code with automated validation
- **Provenance Tracking**: Complete lineage documentation from original field records to final outputs
- **Quality Assurance**: Multi-stage validation using both automated frameworks and expert review
- **Scalability**: Modular architecture supporting future dataset integration and technological evolution
- **Interoperability**: Standards-compliant outputs ensuring compatibility across diverse analytical environments

## 📋 Phase-by-Phase Methodological Approach

### Phase 1: Database Analysis & Profiling

**Analytical Methods:**
- **Automated Schema Profiling**: Quantitative analysis of table structures, data types, and constraint relationships using SQLAlchemy reflection capabilities
- **Join-Dependency Index (JDI) Calculation**: Mathematical assessment of relational complexity to inform denormalization decisions
- **Lookup Inflation Factor (LIF) Analysis**: Quantification of performance impacts from normalized table structures
- **Entity-Relationship Modeling**: Automated ERD generation using Graphviz for visual schema documentation

**Key Techniques:**
```python
# Schema profiling implementation
def profile_database_schema(connection):
    metadata = MetaData()
    metadata.reflect(bind=connection)
    
    # Extract table cardinalities, column statistics, constraint relationships
    schema_metrics = {
        'table_count': len(metadata.tables),
        'relationship_complexity': calculate_jdi(metadata),
        'normalization_level': assess_normal_forms(metadata)
    }
    return schema_metrics
```

**Quality Assurance:**
- Cross-validation of schema extraction against original MS Access structures
- Performance benchmarking using `EXPLAIN ANALYZE` for representative queries
- Expert validation of automated profiling results against historical documentation

### Phase 2: Database Transformation & ETL

**Analytical Methods:**
- **Staged ETL Pipeline**: Multi-step transformation from normalized legacy schemas to denormalized analytical tables
- **Variable-Level Feature Engineering**: Systematic evaluation and transformation of 300+ archaeological variables
- **Controlled Vocabulary Standardization**: Semantic harmonization of categorical variables across database versions
- **Automated Data Quality Validation**: Implementation of Great Expectations framework for continuous quality assurance

**Data Cleaning Techniques:**
```python
# Advanced text normalization for archaeological variables
def normalize_site_designations(text_field):
    # Standardize site/subsite notation using regex patterns
    pattern = r'(\d+):(\d+)([A-Z]?)([WEN]?)(\d*)'
    normalized = re.sub(pattern, standardize_format, text_field)
    return validate_archaeological_context(normalized)
```

**Statistical Methods:**
- **Outlier Detection**: Z-score analysis for artifact count validation
- **Missing Data Analysis**: Pattern recognition for systematic data gaps
- **Cross-Validation**: Comparison of overlapping variables across database versions

### Phase 3: GIS Digitization

**Spatial Digitization Methods:**
- **Manual Feature Extraction**: Systematic digitization of archaeological features from 1:2,000 raster basemaps
- **Topology-Constrained Digitization**: Application of spatial rules to maintain geometric validity
- **Multi-Scale Feature Classification**: Hierarchical categorization of archaeological, environmental, and modern features
- **Quality-Controlled Attribute Assignment**: Standardized provisional schemas with validation rules

**Feature Categories Digitized:**
```
Archaeological Features:
├── Architectural (floors, walls, plazas, staircases)
├── Artifact Concentrations (sherds, obsidian, stone)
├── Excavation Units (pits, trenches, test units)
└── Site Boundaries (compound limits, plaza edges)

Environmental Features:
├── Natural (terraces, drainage, tepetate exposures)
├── Water Management (canals, dams, reservoirs)
└── Topographic (elevation changes, slope breaks)

Modern Features:
├── Infrastructure (roads, railroads, power lines)
├── Land Use (agriculture, urban development)
└── Disturbance (destroyed areas, alterations)
```

**Quality Assurance:**
- QGIS Topology Checker validation for geometric consistency
- Cross-reference with historical photographs and field documentation
- Expert archaeological review of feature interpretation and classification

### Phase 4: Georeferencing & Coordinate Transformation

**High-Precision Georeferencing Methods:**
- **Ground Control Point (GCP) Collection**: Systematic identification of stable features across historical and modern imagery
- **Multi-Order Transformation Analysis**: Comparative evaluation of projective, affine, and polynomial transformations
- **Custom NTv2 Grid Development**: Thin Plate Spline interpolation for precise coordinate system transformation
- **Spatial Accuracy Assessment**: RMSE calculation and spatial autocorrelation analysis of residual errors

**Transformation Pipeline:**
```python
# Custom CRS transformation using NTv2 grids
def transform_millon_to_utm(coordinates):
    # Define custom 'Millon Space' CRS
    millon_crs = CRS.from_proj4('+proj=cart +datum=local +units=m')
    
    # Apply NTv2 grid shift transformation
    transformer = Transformer.from_crs(millon_crs, 'EPSG:32614', 
                                     grid_file='millon_to_utm14n.gsb')
    return transformer.transform(*coordinates)
```

**Statistical Validation:**
- **Root Mean Square Error (RMSE)**: Quantification of transformation accuracy
- **Spatial Error Distribution Analysis**: Identification of systematic vs. random error patterns
- **Moran's I Spatial Autocorrelation**: Detection of clustered error patterns requiring correction

### Phase 5: Geospatial Integration & Feature Engineering

**Spatial Analysis Methods:**
- **Attribute-Geometry Joining**: SQL-based spatial joins between tabular and vector datasets
- **Proportional Overlay Analysis**: Area-weighted attribution for overlapping spatial features
- **Architectural Classification Algorithm**: Rule-based classification using spatial relationships and attribute logic
- **Derived Spatial Metrics**: Calculation of geometric, topological, and density-based variables

**Feature Engineering Techniques:**
```sql
-- Spatial feature engineering in PostGIS
WITH spatial_metrics AS (
  SELECT 
    ssn,
    ST_Area(geom) as tract_area,
    ST_Perimeter(geom) as perimeter,
    ST_Area(geom) / (ST_Perimeter(geom)^2) as shape_complexity,
    ST_Centroid(geom) as centroid_coords
  FROM collection_units
)
SELECT 
  c.*,
  s.tract_area,
  s.shape_complexity,
  ST_X(s.centroid_coords) as utm_x,
  ST_Y(s.centroid_coords) as utm_y
FROM tmp_df12 c
JOIN spatial_metrics s ON c.ssn = s.ssn;
```

**Classification Methods:**
- **Hierarchical Feature Classification**: Multi-level architectural interpretation schema
- **Spatial Overlay Analysis**: Cross-referencing architectural features with collection unit interpretations
- **Weighted Attribution**: Proportional assignment of attributes based on spatial overlap

### Phase 6: Archival Data Preparation

**Metadata Engineering:**
- **Multi-Level Metadata Generation**: Project, dataset, and file-level documentation following tDAR standards
- **Controlled Vocabulary Formalization**: CSV and PDF export of standardized terminology
- **Format Transformation**: Conversion to archival-safe formats (Shapefile, GeoJSON, CSV) with attribute preservation

**Documentation Methods:**
- **Automated Crosswalk Generation**: Mapping between abbreviated Shapefile field names and full descriptive names
- **Provenance Documentation**: Complete transformation lineage from original sources to final outputs
- **User-Centered Tutorial Development**: Step-by-step guides for data integration and analysis

### Phase 7: PostGIS Database Design & Optimization

**Database Architecture Methods:**
- **Hybrid Normalization Strategy**: Selective denormalization optimized for archaeological analytical workflows
- **Spatial Indexing Optimization**: GIST indexes for geometry columns, BRIN indexes for large ordered datasets
- **Query Performance Tuning**: Materialized views for computationally intensive spatial operations
- **Multi-Format Export Pipeline**: Automated generation of API-ready and static file formats

**Performance Optimization:**
```sql
-- Optimized spatial query with indexed lookups
CREATE INDEX CONCURRENTLY idx_geom_gist ON collection_units USING GIST(geom);
CREATE INDEX CONCURRENTLY idx_ceramic_phase ON tmp_df12 USING BTREE(ceramic_phase);

-- Materialized view for common analytical queries
CREATE MATERIALIZED VIEW mv_ceramic_density AS
SELECT 
  c.geom,
  c.ssn,
  (t.total_ceramics / ST_Area(c.geom)) as ceramic_density_per_m2,
  t.ceramic_phase_primary
FROM collection_units c
JOIN tmp_df12 t ON c.ssn = t.ssn
WHERE t.total_ceramics > 0;
```

### Phase 8: Interactive Visualization & Tutorial Development

**Web Mapping Methods:**
- **RESTful API Design**: FastAPI endpoints for curated spatial data access
- **Interactive Cartography**: Leaflet.js implementation with spatial filtering and attribute querying
- **Progressive Data Loading**: Tile-based rendering for large datasets with zoom-dependent detail levels
- **Multi-Platform Tutorial Development**: Jupyter Notebooks, RMarkdown, and PDF guides for diverse user communities

## 🧭 Spatial Processing Workflows

### Coordinate Reference Systems
- **Source CRS**: Custom "Millon Space" (site-centered Cartesian, 15°25′ rotation)
- **Production CRS**: EPSG:32614 (UTM Zone 14N, WGS84) for analytical applications
- **Distribution CRS**: EPSG:4326 (WGS84 Geographic) for web mapping and broad compatibility
- **Custom Transformations**: NTv2 grid files (`.gsb`) for high-precision coordinate conversion

### Georeferencing Process
1. **GCP Collection**: Manual identification using modern satellite imagery and historical map features
2. **Transformation Calibration**: Comparative analysis of projective, affine, and polynomial methods
3. **Grid Generation**: Thin Plate Spline interpolation for continuous transformation surface
4. **Accuracy Validation**: RMSE assessment and spatial error distribution analysis
5. **Production Application**: Batch transformation of all vector and raster datasets

### Quality Assurance Framework
- **Geometric Validation**: ST_IsValid checks with automated ST_MakeValid corrections
- **Topological Consistency**: Gap and overlap detection with automated repair workflows
- **Attribute Validation**: Great Expectations rules for data type, range, and pattern compliance
- **Cross-Validation**: Comparison between spatial and tabular data for consistency verification

## 🧮 Analytical & Statistical Methods

### Feature Engineering Approaches
- **Geometric Metrics**: Area, perimeter, shape complexity, centroid coordinates
- **Density Calculations**: Artifact counts per unit area, spatial concentration indices
- **Proximity Analysis**: Distance to architectural features, site boundaries, and environmental zones
- **Temporal Attribution**: Ceramic phase assignment with confidence scoring

### Classification Algorithms
- **Rule-Based Classification**: Expert-defined logic for architectural feature interpretation
- **Spatial Decision Trees**: Hierarchical classification using geometric and contextual variables
- **Proportional Attribution**: Area-weighted assignment for overlapping spatial features
- **Confidence Scoring**: Uncertainty quantification for derived classifications

### Statistical Validation Methods
- **Cross-Validation**: K-fold validation for predictive models and classification algorithms
- **Spatial Autocorrelation**: Moran's I and Local Indicators of Spatial Association (LISA)
- **Error Propagation**: Uncertainty quantification through transformation pipelines
- **Sensitivity Analysis**: Robustness testing for georeferencing and classification parameters

## 🧰 Tools & Libraries by Analytical Domain

### Database & ETL Processing
| Tool/Library | Purpose | Phase Application |
|--------------|---------|-------------------|
| `SQLAlchemy` | Database reflection and ORM | Phase 1: Schema analysis |
| `pandas` | Tabular data manipulation | Phase 2: ETL and cleaning |
| `Great Expectations` | Data quality validation | Phase 2: Automated QA |
| `psycopg2` | PostgreSQL connectivity | Phase 1-2: Database operations |

### Geospatial Analysis
| Tool/Library | Purpose | Phase Application |
|--------------|---------|-------------------|
| `GeoPandas` | Vector data processing | Phase 3-5: Spatial analysis |
| `Shapely` | Geometric operations | Phase 3-5: Geometry validation |
| `Rasterio` | Raster data handling | Phase 4: Georeferencing |
| `GDAL/OGR` | Format conversion and transformation | Phase 3-4: Data processing |
| `pyproj` | Coordinate transformation | Phase 4: CRS operations |

### Spatial Database & Deployment
| Tool/Library | Purpose | Phase Application |
|--------------|---------|-------------------|
| `PostGIS` | Spatial database functions | Phase 5-7: Spatial operations |
| `FastAPI` | RESTful API development | Phase 7-8: Data serving |
| `Docker` | Containerized deployment | Phase 7: Database distribution |
| `Leaflet.js` | Interactive web mapping | Phase 8: Visualization |

### Statistical & Validation
| Tool/Library | Purpose | Phase Application |
|--------------|---------|-------------------|
| `scipy.stats` | Statistical analysis | Phase 1-4: Error assessment |
| `scikit-learn` | Machine learning validation | Phase 2-5: Classification |
| `matplotlib/plotly` | Visualization and diagnostics | All phases: Quality assurance |

### Documentation & Archival
| Tool/Library | Purpose | Phase Application |
|--------------|---------|-------------------|
| `Pandoc` | Documentation generation | Phase 6: Tutorial development |
| `Graphviz` | Schema visualization | Phase 1: ERD generation |
| `7-Zip` | Archival compression | Phase 6: Package preparation |

This comprehensive methodological framework ensures that the Digital TMP project maintains the highest standards of archaeological data science while producing outputs that serve diverse research communities and preserve the legacy of the Teotihuacan Mapping Project for future generations.