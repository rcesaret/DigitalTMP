# 🧠 Methods & Analytical Approach

> **Purpose:** Explain the modeling, spatial, and analytical methods used across the project phases.

## 📊 Data Processing
Describe preprocessing steps taken:
- Data cleaning and standardization
- Handling missing values
- Merging disparate tables or geospatial layers

> _Tip_: Break down by phase if needed.

## 🧭 Spatial Processing
Document your geospatial workflows:
- Coordinate systems used (e.g., EPSG codes)
- Georeferencing process for raster images
- Digitization of shapefiles
- CRS transformations and alignment

> _Example_:  
> All vector files were transformed to EPSG:4326 for integration with web mapping tools.

## 🧮 Modeling / Analysis
Explain analytical or statistical steps:
- Feature engineering (spatial joins, distances, z-scores)
- Statistical models (regression, clustering, etc.)
- Machine learning pipelines (if any)
- Parameter tuning methods (e.g., grid search, cross-validation)

## 🧰 Tools & Libraries

| Tool/Library | Purpose |
|--------------|---------|
| `pandas`     | Data wrangling |
| `geopandas`  | Vector data |
| `rasterio`   | Raster processing |
| `sf` (R)     | Spatial joins, CRS fixes |
| `SQL` / PostGIS | Queries, spatial validation |
