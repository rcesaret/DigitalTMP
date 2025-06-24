# Digital TMP - CRS Catalogue (Draft v1.0 -- 6/24/2025)

---
**Author:** Rudolf Cesaretti
**Affiliation:** ASU Teotihuacan Research Laboratory
**Date:** June 24, 2025
**Version:** v1.0
---

## Overview & Summary



---

## Project Geodetic CRSs


---

### CRS Catalogue Table

| **Code**        | **Source** | **CodeNum** | **Name**                        | **Area_of_Use**                                                                                                                                         | **Type**      | **Datum**                                                        | **Geodetic_Base_CRS**            | **Ellipsoid**                                | **Unit** | **RevisionDate** | **spatialreference.org_URL**                  | **epsg.org_URL**                                                                  | **epsg.io_URL**        | **Scope**                                           |
|-----------------|------------|-------------|---------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------|---------------|------------------------------------------------------------------|----------------------------------|----------------------------------------------|----------|------------------|-----------------------------------------------|-----------------------------------------------------------------------------------|------------------------|-----------------------------------------------------|
| **EPSG:3857**   | EPSG       | 3857        | WGS 84 / Pseudo-Mercator        | World between 85.06°S and 85.06°N.                                                                                                                      | Projected     | World Geodetic System 1984 ensemble (https://epsg.io/6326-datum) | EPSG:4326 (https://epsg.io/4326) | WGS 84                                       | metre    | 3/14/2020        | https://spatialreference.org/ref/epsg/3857/   | https://epsg.org/crs_3857/WGS-84-Pseudo-Mercator.html?sessionkey=be1cz55on7       | https://epsg.io/3857   | Web mapping and visualisation.                      |
| **EPSG:4326**   | EPSG       | 4326        | WGS 84                          | World                                                                                                                                                   | Geographic 2D | World Geodetic System 1984 ensemble (https://epsg.io/6326-datum) | EPSG:4979 (https://epsg.io/4979) | WGS 84                                       | degree   | 11/29/2022       | https://spatialreference.org/ref/epsg/4326/   | https://epsg.org/crs_4326/WGS-84.html?sessionkey=be1cz55on7                       | https://epsg.io/4326   | Web mapping and visualisation.                      |
| **EPSG:4487**   | EPSG       | 4487        | Mexico ITRF92 / UTM zone 14N    | Mexico between 102°W and 96°W, onshore and offshore.                                                                                                    | Projected     | Mexico ITRF92 (https://epsg.io/1042-datum)                       | EPSG:4483 (https://epsg.io/4483) | GRS 1980 (https://epsg.io/7019-ellipsoid)    | metre    | 11/19/2023       | https://spatialreference.org/ref/epsg/4487/   | https://epsg.org/crs_4487/Mexico-ITRF92-UTM-zone-14N.html?sessionkey=be1cz55on7   | https://epsg.io/4487   | Engineering survey, topographic mapping.            |
| **EPSG:6369**   | EPSG       | 6369        | Mexico ITRF2008 / UTM zone 14N  | Mexico between 102°W and 96°W, onshore and offshore.                                                                                                    | Projected     | Mexico ITRF2008 (https://epsg.io/1120-datum)                     | EPSG:6365 (https://epsg.io/6365) | GRS 1980 (https://epsg.io/7019-ellipsoid)    | metre    | 11/19/2023       | https://spatialreference.org/ref/epsg/6369/   | https://epsg.org/crs_6369/Mexico-ITRF2008-UTM-zone-14N.html?sessionkey=be1cz55on7 | https://epsg.io/6369   | Engineering survey, topographic mapping.            |
| **EPSG:26714**  | EPSG       | 26714       | NAD27 / UTM zone 14N            | North America - between 102°W and 96°W. Onshore for Mexican Pacific coast but onshore and offshore for US & Mexico Gulf of Mexico and Caribbean coasts. | Projected     | North American Datum 1927 (https://epsg.io/6267-datum)           | EPSG:4267 (https://epsg.io/4267) | Clarke 1866 (https://epsg.io/7008-ellipsoid) | metre    | 9/10/2021        | https://spatialreference.org/ref/epsg/26714/  | https://epsg.org/crs_26714/NAD27-UTM-zone-14N.html?sessionkey=be5rdkd67s          | https://epsg.io/26714  | Engineering survey, topographic mapping.            |
| **EPSG:26914**  | EPSG       | 26914       | NAD83 / UTM zone 14N            | North America - between 102°W and 96°W - onshore and offshore.                                                                                          | Projected     | North American Datum 1983 (https://epsg.io/6269-datum)           | EPSG:4269 (https://epsg.io/4269) | GRS 1980 (https://epsg.io/7019-ellipsoid)    | metre    | 3/14/2020        | https://spatialreference.org/ref/epsg/26914/  | https://epsg.org/crs_26914/NAD83-UTM-zone-14N.html?sessionkey=be1cz55on7          | https://epsg.io/26914  | Engineering survey, topographic mapping.            |
| **EPSG:31968**  | EPSG       | 31968       | SIRGAS 2000 / UTM zone 14N      | Latin America between 102°W and 96°W, northern hemisphere, onshore and offshore.                                                                        | Projected     | SIRGAS 2000 (https://epsg.io/6674-datum)                         | EPSG:4674 (https://epsg.io/4674) | GRS 1980 (https://epsg.io/7019-ellipsoid)    | metre    | 9/23/2021        | https://spatialreference.org/ref/epsg/31968/  | https://epsg.org/crs_31968/SIRGAS-2000-UTM-zone-14N.html?sessionkey=r9vj7il904    | https://epsg.io/31968  | Engineering survey, topographic mapping.            |
| **EPSG:32614**  | EPSG       | 32614       | WGS 84 / UTM zone 14N           | Between 102°W and 96°W, northern hemisphere between equator and 84°N, onshore and offshore. Mexico.                                                     | Projected     | World Geodetic System 1984 ensemble (https://epsg.io/6326-datum) | EPSG:4326 (https://epsg.io/4326) | WGS 84                                       | metre    | 12/12/2022       | https://spatialreference.org/ref/epsg/32614/  | https://epsg.org/crs_32614/WGS-84-UTM-zone-14N.html?sessionkey=f0oef4ce06         | https://epsg.io/32614  | Navigation and medium accuracy spatial referencing. |
| **ESRI:103797** | ESRI       | 103797      | Mexican_Datum_1993_UTM_Zone_14N | Mexico between 102°W and 96°W, onshore and offshore.                                                                                                    | Projected     | Mexico ITRF92 (https://epsg.io/1042-datum)                       | NA                               | GRS 1980 (https://epsg.io/7019-ellipsoid)    | metre    | NA               | https://spatialreference.org/ref/esri/103797/ | NA                                                                                | https://epsg.io/103797 | Engineering survey, topographic mapping.            |

#### Notes on CRSs

- **EPSG:3857 --** Used in projected and engineering coordinate reference systems. Not a recognised geodetic system. Uses spherical development of ellipsoidal coordinates. Relative to WGS 84 / World Mercator (CRS code 3395) gives errors of 0.7 percent in scale and differences in northing of up to 43km in the map (21km on the ground).
- **EPSG:4487 --** Approximation at the +/- 1m level assuming that Mexico ITRF92 is equivalent to WGS 84. Replaces NAD27 / UTM zone 14N (CRS code 26714). Replaced by Mexico ITRF2008 / UTM zone 14N (CRS code 6369) from December 2010.
- **EPSG:6369 --** Approximation at the +/- 1m level assuming that Mexico ITRF2008 is equivalent to WGS 84. Replaces Mexico ITRF92 / UTM zone 14N (CRS code 4487) from December 2010.
- **EPSG:26714 --** Parameter files are from NAD27 to NAD83 (1) (code 1241) assuming that NAD83 is equivalent to WGS 84 within the accuracy of this tfm. Uses NADCON method which expects longitudes positive west; EPSG CRS codes 4267 and 4326 have longitudes positive east. See NAD27 / BLM 14N (ftUS) (code 32064) for non-metric equivalent used in US Gulf of Mexico. In Mexico, replaced by Mexicand Datum of 1993 / UTM zone 14N (code 4487). In Canada and USA, replaced by NAD83 / UTM zone 14N (code 26914).
- **EPSG:26914 --** Derived at 354 stations. Accuracy 2m in each axis. Replaces NAD27 / UTM zone 14N. For accuracies better than 1m replaced by NAD83(CSRS) / UTM zone 14N in Canada and NAD83(HARN) / UTM zone 14N in US.

---

### CRS Catalogue with File Formats

#### EPSG:3857

- **Name:** WGS 84 / Pseudo-Mercator
- **Code:** EPSG:3857
- **Source:** EPSG
- **CodeNum:** 3857
- **Area of Use:** World between 85.06°S and 85.06°N.
- **Type:** Projected
- **Datum:** World Geodetic System 1984 ensemble (https://epsg.io/6326-datum)
- **Geodetic Base CRS:** EPSG:4326 (https://epsg.io/4326)
- **Ellipsoid:** WGS 84
- **Unit:** metre
- **RevisionDate:** 3/14/2020
- **spatialreference.org URL:** https://spatialreference.org/ref/epsg/3857/
- **epsg.org URL:** https://epsg.org/crs_3857/WGS-84-Pseudo-Mercator.html?sessionkey=be1cz55on7
- **epsg.io URL:** https://epsg.io/3857
- **Remarks:** Used in projected and engineering coordinate reference systems. Not a recognised geodetic system. Uses spherical development of ellipsoidal coordinates. Relative to WGS 84 / World Mercator (CRS code 3395) gives errors of 0.7 percent in scale and differences in northing of up to 43km in the map (21km on the ground).
- **Scope:** Web mapping and visualisation.

##### WKT2

```
PROJCRS["WGS 84 / Pseudo-Mercator",
    BASEGEOGCRS["WGS 84",
        ENSEMBLE["World Geodetic System 1984 ensemble",
            MEMBER["World Geodetic System 1984 (Transit)"],
            MEMBER["World Geodetic System 1984 (G730)"],
            MEMBER["World Geodetic System 1984 (G873)"],
            MEMBER["World Geodetic System 1984 (G1150)"],
            MEMBER["World Geodetic System 1984 (G1674)"],
            MEMBER["World Geodetic System 1984 (G1762)"],
            MEMBER["World Geodetic System 1984 (G2139)"],
            MEMBER["World Geodetic System 1984 (G2296)"],
            ELLIPSOID["WGS 84",6378137,298.257223563,
                LENGTHUNIT["metre",1]],
            ENSEMBLEACCURACY[2.0]],
        PRIMEM["Greenwich",0,
            ANGLEUNIT["degree",0.0174532925199433]],
        ID["EPSG",4326]],
    CONVERSION["Popular Visualisation Pseudo-Mercator",
        METHOD["Popular Visualisation Pseudo Mercator",
            ID["EPSG",1024]],
        PARAMETER["Latitude of natural origin",0,
            ANGLEUNIT["degree",0.0174532925199433],
            ID["EPSG",8801]],
        PARAMETER["Longitude of natural origin",0,
            ANGLEUNIT["degree",0.0174532925199433],
            ID["EPSG",8802]],
        PARAMETER["False easting",0,
            LENGTHUNIT["metre",1],
            ID["EPSG",8806]],
        PARAMETER["False northing",0,
            LENGTHUNIT["metre",1],
            ID["EPSG",8807]]],
    CS[Cartesian,2],
        AXIS["easting (X)",east,
            ORDER[1],
            LENGTHUNIT["metre",1]],
        AXIS["northing (Y)",north,
            ORDER[2],
            LENGTHUNIT["metre",1]],
    USAGE[
        SCOPE["Web mapping and visualisation."],
        AREA["World between 85.06°S and 85.06°N."],
        BBOX[-85.06,-180,85.06,180]],
    ID["EPSG",3857]]
```

##### PROJ `.json` file

```
{"$schema":"https://proj.org/schemas/v0.7/projjson.schema.json","type":"ProjectedCRS","name":"WGS 84 / Pseudo-Mercator","base_crs":{"type":"GeographicCRS","name":"WGS 84","datum_ensemble":{"name":"World Geodetic System 1984 ensemble","members":[{"name":"World Geodetic System 1984 (Transit)","id":{"authority":"EPSG","code":1166}},{"name":"World Geodetic System 1984 (G730)","id":{"authority":"EPSG","code":1152}},{"name":"World Geodetic System 1984 (G873)","id":{"authority":"EPSG","code":1153}},{"name":"World Geodetic System 1984 (G1150)","id":{"authority":"EPSG","code":1154}},{"name":"World Geodetic System 1984 (G1674)","id":{"authority":"EPSG","code":1155}},{"name":"World Geodetic System 1984 (G1762)","id":{"authority":"EPSG","code":1156}},{"name":"World Geodetic System 1984 (G2139)","id":{"authority":"EPSG","code":1309}},{"name":"World Geodetic System 1984 (G2296)","id":{"authority":"EPSG","code":1383}}],"ellipsoid":{"name":"WGS 84","semi_major_axis":6378137,"inverse_flattening":298.257223563},"accuracy":"2.0","id":{"authority":"EPSG","code":6326}},"coordinate_system":{"subtype":"ellipsoidal","axis":[{"name":"Geodetic latitude","abbreviation":"Lat","direction":"north","unit":"degree"},{"name":"Geodetic longitude","abbreviation":"Lon","direction":"east","unit":"degree"}]},"id":{"authority":"EPSG","code":4326}},"conversion":{"name":"Popular Visualisation Pseudo-Mercator","method":{"name":"Popular Visualisation Pseudo Mercator","id":{"authority":"EPSG","code":1024}},"parameters":[{"name":"Latitude of natural origin","value":0,"unit":"degree","id":{"authority":"EPSG","code":8801}},{"name":"Longitude of natural origin","value":0,"unit":"degree","id":{"authority":"EPSG","code":8802}},{"name":"False easting","value":0,"unit":"metre","id":{"authority":"EPSG","code":8806}},{"name":"False northing","value":0,"unit":"metre","id":{"authority":"EPSG","code":8807}}]},"coordinate_system":{"subtype":"Cartesian","axis":[{"name":"Easting","abbreviation":"X","direction":"east","unit":"metre"},{"name":"Northing","abbreviation":"Y","direction":"north","unit":"metre"}]},"scope":"Web mapping and visualisation.","area":"World between 85.06°S and 85.06°N.","bbox":{"south_latitude":-85.06,"west_longitude":-180,"north_latitude":85.06,"east_longitude":180},"id":{"authority":"EPSG","code":3857}}
```

##### ESRI WKT

```
PROJCS["WGS_1984_Web_Mercator_Auxiliary_Sphere",GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137.0,298.257223563]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],PROJECTION["Mercator_Auxiliary_Sphere"],PARAMETER["False_Easting",0.0],PARAMETER["False_Northing",0.0],PARAMETER["Central_Meridian",0.0],PARAMETER["Standard_Parallel_1",0.0],PARAMETER["Auxiliary_Sphere_Type",0.0],UNIT["Meter",1.0]]
```

##### `.prj` file

```
PROJCS["WGS_1984_Web_Mercator_Auxiliary_Sphere",GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137.0,298.257223563]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],PROJECTION["Mercator_Auxiliary_Sphere"],PARAMETER["False_Easting",0.0],PARAMETER["False_Northing",0.0],PARAMETER["Central_Meridian",0.0],PARAMETER["Standard_Parallel_1",0.0],PARAMETER["Auxiliary_Sphere_Type",0.0],UNIT["Meter",1.0]]

```

---

#### EPSG:4326

- **Name:**
- **Code:**
- **Source:**
- **CodeNum:**
- **Area of Use:**
- **Type:**
- **Datum:**
- **Geodetic Base CRS:**
- **Ellipsoid:**
- **Unit:**
- **RevisionDate:**
- **spatialreference.org URL:**
- **epsg.org URL:**
- **epsg.io URL:**
- **Remarks:**
- **Scope:**

##### WKT2

##### PROJ `.json` file

##### ESRI WKT

##### `.prj` file

---

#### EPSG:4487

- **Name:**
- **Code:**
- **Source:**
- **CodeNum:**
- **Area of Use:**
- **Type:**
- **Datum:**
- **Geodetic Base CRS:**
- **Ellipsoid:**
- **Unit:**
- **RevisionDate:**
- **spatialreference.org URL:**
- **epsg.org URL:**
- **epsg.io URL:**
- **Remarks:**
- **Scope:**

##### WKT2

##### PROJ `.json` file

##### ESRI WKT

##### `.prj` file

---

#### EPSG:6369

- **Name:**
- **Code:**
- **Source:**
- **CodeNum:**
- **Area of Use:**
- **Type:**
- **Datum:**
- **Geodetic Base CRS:**
- **Ellipsoid:**
- **Unit:**
- **RevisionDate:**
- **spatialreference.org URL:**
- **epsg.org URL:**
- **epsg.io URL:**
- **Remarks:**
- **Scope:**

##### WKT2

##### PROJ `.json` file

##### ESRI WKT

##### `.prj` file

---

#### EPSG:26714

- **Name:**
- **Code:**
- **Source:**
- **CodeNum:**
- **Area of Use:**
- **Type:**
- **Datum:**
- **Geodetic Base CRS:**
- **Ellipsoid:**
- **Unit:**
- **RevisionDate:**
- **spatialreference.org URL:**
- **epsg.org URL:**
- **epsg.io URL:**
- **Remarks:**
- **Scope:**

##### WKT2

##### PROJ `.json` file

##### ESRI WKT

##### `.prj` file

---

#### EPSG:26914

- **Name:**
- **Code:**
- **Source:**
- **CodeNum:**
- **Area of Use:**
- **Type:**
- **Datum:**
- **Geodetic Base CRS:**
- **Ellipsoid:**
- **Unit:**
- **RevisionDate:**
- **spatialreference.org URL:**
- **epsg.org URL:**
- **epsg.io URL:**
- **Remarks:**
- **Scope:**

##### WKT2

##### PROJ `.json` file

##### ESRI WKT

##### `.prj` file

---

#### EPSG:31968

- **Name:**
- **Code:**
- **Source:**
- **CodeNum:**
- **Area of Use:**
- **Type:**
- **Datum:**
- **Geodetic Base CRS:**
- **Ellipsoid:**
- **Unit:**
- **RevisionDate:**
- **spatialreference.org URL:**
- **epsg.org URL:**
- **epsg.io URL:**
- **Remarks:**
- **Scope:**

##### WKT2

##### PROJ `.json` file

##### ESRI WKT

##### `.prj` file

---

#### EPSG:32614

- **Name:**
- **Code:**
- **Source:**
- **CodeNum:**
- **Area of Use:**
- **Type:**
- **Datum:**
- **Geodetic Base CRS:**
- **Ellipsoid:**
- **Unit:**
- **RevisionDate:**
- **spatialreference.org URL:**
- **epsg.org URL:**
- **epsg.io URL:**
- **Remarks:**
- **Scope:**

##### WKT2

##### PROJ `.json` file

##### ESRI WKT

##### `.prj` file

---

#### ESRI:103797

- **Name:**
- **Code:**
- **Source:**
- **CodeNum:**
- **Area of Use:**
- **Type:**
- **Datum:**
- **Geodetic Base CRS:**
- **Ellipsoid:**
- **Unit:**
- **RevisionDate:**
- **spatialreference.org URL:**
- **epsg.org URL:**
- **epsg.io URL:**
- **Remarks:**
- **Scope:**

##### WKT2

##### PROJ `.json` file

##### ESRI WKT

##### `.prj` file

---

## Custom Teotihuacan Mapping Project (TMP) CRSs for 'Millon Space'

#### TMP:1000000

- **Name:**
- **Code:**
- **Source:**
- **CodeNum:**
- **Area of Use:**
- **Type:**
- **Datum:**
- **Geodetic Base CRS:**
- **Ellipsoid:**
- **Unit:**
- **RevisionDate:**
- **Remarks:**
- **Scope:**

##### WKT2

##### PROJ `.json` file

##### ESRI WKT

##### `.prj` file

---

#### TMP:1000001

- **Name:**
- **Code:**
- **Source:**
- **CodeNum:**
- **Area of Use:**
- **Type:**
- **Datum:**
- **Geodetic Base CRS:**
- **Ellipsoid:**
- **Unit:**
- **RevisionDate:**
- **Remarks:**
- **Scope:**

##### WKT2

##### PROJ `.json` file

##### ESRI WKT

##### `.prj` file

---
