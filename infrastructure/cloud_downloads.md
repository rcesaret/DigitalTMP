
# 🛰 External File Downloads (Large Assets)

> **Purpose:** List all large external files (raster, databases, etc.) and explain how to access/download them.

This project relies on large files not stored in this repo due to GitHub storage limits.

## 📦 Download Instructions

### Option 1: Manual Download

| File | Description | Format | Size | Link |
|------|-------------|--------|------|------|
| `zoning_maps.tif` | Scanned historical zoning | TIFF | 2.4 GB | [Dropbox](https://...) |
| `infrastructure.mdb` | MS Access database | MDB | 600 MB | [Google Drive](https://...) |
| `final_postgis.dump` | PostgreSQL database dump | SQL | 1.1 GB | [S3](https://...) |

### Option 2: Scripted Download (Preferred)

Run this script from the root directory:

```bash
bash scripts/download_big_files.sh
```

