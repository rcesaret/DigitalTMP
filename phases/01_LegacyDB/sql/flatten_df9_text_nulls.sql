-- =================================================================================
--   Flattening Query for TMP_DF9 Benchmark Database with Text and NULL Conversion
-- =================================================================================
-- File: `flatten_df9_text_nulls.sql`
-- Date: 2025-06-10
-- Author: Rudolf Cesaretti
-- Version: v1
--
-- Description:
-- This query joins the 18 core data tables from the tmp_df9 schema into a
-- single wide-format table. It uses LEFT JOINs from the central "tblSSN"
-- table to ensure all site records are preserved.
--
-- All columns are explicitly aliased to prevent name collisions and provide
-- clarity on the origin of each field in the final flattened table.
--
-- It builds upon the previous version (`flatten_df9.sql`) by adding three key 
-- transformations:
-- 1.  Coded values (integers) are replaced with their corresponding text
--     descriptions by joining the appropriate 'Codes_' lookup tables.
-- 2.  Specified NA values (e.g., -1, -999, 'NONE') are converted to
--     standard SQL NULL values for analytical consistency.
-- 3.  Modified all code-to-text conversions to prepend the numeric code
--     to the description, in the format: "<code>. <description>".
-- =================================================================================

WITH
"pivoted_fieldWorkers" AS (
  SELECT
    "SSN",
    BOOL_OR("personnelCode" = 1) AS "fieldWorkers_Millon_R",
    BOOL_OR("personnelCode" = 2) AS "fieldWorkers_Drewitt_B",
    BOOL_OR("personnelCode" = 3) AS "fieldWorkers_Bennyhoff",
    BOOL_OR("personnelCode" = 4) AS "fieldWorkers_Banos",
    BOOL_OR("personnelCode" = 5) AS "fieldWorkers_Cowgill",
    BOOL_OR("personnelCode" = 6) AS "fieldWorkers_Spence",
    BOOL_OR("personnelCode" = 7) AS "fieldWorkers_Wallrath",
    BOOL_OR("personnelCode" = 8) AS "fieldWorkers_Marino",
    BOOL_OR("personnelCode" = 9) AS "fieldWorkers_Barbour",
    BOOL_OR("personnelCode" = 10) AS "fieldWorkers_deLucio_A",
    BOOL_OR("personnelCode" = 11) AS "fieldWorkers_deLucio_J",
    BOOL_OR("personnelCode" = 12) AS "fieldWorkers_Blucher",
    BOOL_OR("personnelCode" = 13) AS "fieldWorkers_Hungerford",
    BOOL_OR("personnelCode" = 14) AS "fieldWorkers_Sutherland",
    BOOL_OR("personnelCode" = 15) AS "fieldWorkers_Wilkerson",
    BOOL_OR("personnelCode" = 16) AS "fieldWorkers_Sharnoff",
    BOOL_OR("personnelCode" = 17) AS "fieldWorkers_Sanchez",
    BOOL_OR("personnelCode" = 18) AS "fieldWorkers_Fletcher",
    BOOL_OR("personnelCode" = 19) AS "fieldWorkers_Kolb",
    BOOL_OR("personnelCode" = 20) AS "fieldWorkers_Millon_C",
    BOOL_OR("personnelCode" = 21) AS "fieldWorkers_Dow",
    BOOL_OR("personnelCode" = 22) AS "fieldWorkers_deLucio_M",
    BOOL_OR("personnelCode" = 23) AS "fieldWorkers_Shankman",
    BOOL_OR("personnelCode" = 24) AS "fieldWorkers_Dodds",
    BOOL_OR("personnelCode" = 26) AS "fieldWorkers_Quisenberry",
    BOOL_OR("personnelCode" = 27) AS "fieldWorkers_West_M",
    BOOL_OR("personnelCode" = 28) AS "fieldWorkers_Bruhns_D",
    BOOL_OR("personnelCode" = 29) AS "fieldWorkers_Bruhns_K",
    BOOL_OR("personnelCode" = 30) AS "fieldWorkers_Duran"
  FROM
    tmp_df9."fieldWorkers"
  GROUP BY
    "SSN"
),
"pivoted_labAnalysts" AS (
  SELECT
    "SSN",
    BOOL_OR("personnelCode" = 1) AS "labAnalysts_Millon_R",
    BOOL_OR("personnelCode" = 2) AS "labAnalysts_Drewitt_B",
    BOOL_OR("personnelCode" = 3) AS "labAnalysts_Bennyhoff",
    BOOL_OR("personnelCode" = 4) AS "labAnalysts_Banos",
    BOOL_OR("personnelCode" = 5) AS "labAnalysts_Cowgill",
    BOOL_OR("personnelCode" = 6) AS "labAnalysts_Spence",
    BOOL_OR("personnelCode" = 7) AS "labAnalysts_Wallrath",
    BOOL_OR("personnelCode" = 8) AS "labAnalysts_Marino",
    BOOL_OR("personnelCode" = 9) AS "labAnalysts_Barbour",
    BOOL_OR("personnelCode" = 10) AS "labAnalysts_deLucio_A",
    BOOL_OR("personnelCode" = 11) AS "labAnalysts_deLucio_J",
    BOOL_OR("personnelCode" = 12) AS "labAnalysts_Blucher",
    BOOL_OR("personnelCode" = 13) AS "labAnalysts_Hungerford",
    BOOL_OR("personnelCode" = 14) AS "labAnalysts_Sutherland",
    BOOL_OR("personnelCode" = 15) AS "labAnalysts_Wilkerson",
    BOOL_OR("personnelCode" = 16) AS "labAnalysts_Sharnoff",
    BOOL_OR("personnelCode" = 17) AS "labAnalysts_Sanchez",
    BOOL_OR("personnelCode" = 18) AS "labAnalysts_Fletcher",
    BOOL_OR("personnelCode" = 19) AS "labAnalysts_Kolb",
    BOOL_OR("personnelCode" = 25) AS "labAnalysts_Drewitt_W",
    BOOL_OR("personnelCode" = 26) AS "labAnalysts_Quisenberry",
    BOOL_OR("personnelCode" = 27) AS "labAnalysts_West_M",
    BOOL_OR("personnelCode" = 30) AS "labAnalysts_Duran",
    BOOL_OR("personnelCode" = 31) AS "labAnalysts_West_E"
  FROM
    tmp_df9."labAnalysts"
  GROUP BY
    "SSN"
)
SELECT
    t1."SSN" AS "SSN",
    t1."site" AS "site",
    NULLIF(t1."subsite", 'NONE') AS "subsite",
    t1."unit" AS "unit",
    NULLIF(t1."northing", -999) AS "northing",
    NULLIF(t1."easting", -999) AS "easting",
    NULLIF(t4."collectionYear", -1) AS "collectionYear",
    CASE WHEN t4."collectionQuarter" = -1 THEN NULL ELSE t4."collectionQuarter"::TEXT || '. ' || c_quarter."description" END AS "collectionQuarter",
    COALESCE(t11."fieldWorkers_Millon_R", FALSE) AS "fieldWorkers_Millon_R",
    COALESCE(t11."fieldWorkers_Drewitt_B", FALSE) AS "fieldWorkers_Drewitt_B",
    COALESCE(t11."fieldWorkers_Bennyhoff", FALSE) AS "fieldWorkers_Bennyhoff",
    COALESCE(t11."fieldWorkers_Banos", FALSE) AS "fieldWorkers_Banos",
    COALESCE(t11."fieldWorkers_Cowgill", FALSE) AS "fieldWorkers_Cowgill",
    COALESCE(t11."fieldWorkers_Spence", FALSE) AS "fieldWorkers_Spence",
    COALESCE(t11."fieldWorkers_Wallrath", FALSE) AS "fieldWorkers_Wallrath",
    COALESCE(t11."fieldWorkers_Marino", FALSE) AS "fieldWorkers_Marino",
    COALESCE(t11."fieldWorkers_Barbour", FALSE) AS "fieldWorkers_Barbour",
    COALESCE(t11."fieldWorkers_deLucio_A", FALSE) AS "fieldWorkers_deLucio_A",
    COALESCE(t11."fieldWorkers_deLucio_J", FALSE) AS "fieldWorkers_deLucio_J",
    COALESCE(t11."fieldWorkers_Blucher", FALSE) AS "fieldWorkers_Blucher",
    COALESCE(t11."fieldWorkers_Hungerford", FALSE) AS "fieldWorkers_Hungerford",
    COALESCE(t11."fieldWorkers_Sutherland", FALSE) AS "fieldWorkers_Sutherland",
    COALESCE(t11."fieldWorkers_Wilkerson", FALSE) AS "fieldWorkers_Wilkerson",
    COALESCE(t11."fieldWorkers_Sharnoff", FALSE) AS "fieldWorkers_Sharnoff",
    COALESCE(t11."fieldWorkers_Sanchez", FALSE) AS "fieldWorkers_Sanchez",
    COALESCE(t11."fieldWorkers_Fletcher", FALSE) AS "fieldWorkers_Fletcher",
    COALESCE(t11."fieldWorkers_Kolb", FALSE) AS "fieldWorkers_Kolb",
    COALESCE(t11."fieldWorkers_Millon_C", FALSE) AS "fieldWorkers_Millon_C",
    COALESCE(t11."fieldWorkers_Dow", FALSE) AS "fieldWorkers_Dow",
    COALESCE(t11."fieldWorkers_deLucio_M", FALSE) AS "fieldWorkers_deLucio_M",
    COALESCE(t11."fieldWorkers_Shankman", FALSE) AS "fieldWorkers_Shankman",
    COALESCE(t11."fieldWorkers_Dodds", FALSE) AS "fieldWorkers_Dodds",
    COALESCE(t11."fieldWorkers_Quisenberry", FALSE) AS "fieldWorkers_Quisenberry",
    COALESCE(t11."fieldWorkers_West_M", FALSE) AS "fieldWorkers_West_M",
    COALESCE(t11."fieldWorkers_Bruhns_D", FALSE) AS "fieldWorkers_Bruhns_D",
    COALESCE(t11."fieldWorkers_Bruhns_K", FALSE) AS "fieldWorkers_Bruhns_K",
    COALESCE(t11."fieldWorkers_Duran", FALSE) AS "fieldWorkers_Duran",
    CASE WHEN t2."lastBuildPhase" = -1 THEN NULL ELSE t2."lastBuildPhase"::TEXT || '. ' || c_lastbuildphase."description" END AS "lastBuildPhase",
    CASE WHEN t2."burials" = -1 THEN NULL ELSE t2."burials"::TEXT || '. ' || c_burials."description" END AS "burials",
    CASE WHEN t2."midden" = -1 THEN NULL ELSE t2."midden"::TEXT || '. ' || c_midden."description" END AS "midden",
    CASE WHEN t15."stoneQuant" = -1 THEN NULL ELSE t15."stoneQuant"::TEXT || '. ' || c_stonequant."description" END AS "stoneQuant",
    CASE WHEN t15."stoneDist" = -1 THEN NULL ELSE t15."stoneDist"::TEXT || '. ' || c_stonedist."description" END AS "stoneDist",
    CASE WHEN t15."stoneCut" = -1 THEN NULL ELSE t15."stoneCut"::TEXT || '. ' || c_materials."description" END AS "stoneCut",
    CASE WHEN t15."lajas" = -1 THEN NULL ELSE t15."lajas"::TEXT || '. ' || c_materials_lajas."description" END AS "lajas",
    CASE WHEN t15."tepetate" = -1 THEN NULL ELSE t15."tepetate"::TEXT || '. ' || c_materials_tepetate."description" END AS "tepetate",
    CASE WHEN t15."adobe" = -1 THEN NULL ELSE t15."adobe"::TEXT || '. ' || c_materials_adobe."description" END AS "adobe",
    CASE WHEN t15."xalnene" = -1 THEN NULL ELSE t15."xalnene"::TEXT || '. ' || c_materials_xalnene."description" END AS "xalnene",
    CASE WHEN t15."cascajo" = -1 THEN NULL ELSE t15."cascajo"::TEXT || '. ' || c_materials_cascajo."description" END AS "cascajo",
    CASE WHEN t15."concrete" = -1 THEN NULL ELSE t15."concrete"::TEXT || '. ' || c_materials_concrete."description" END AS "concrete",
    CASE WHEN t15."plasterUnpaint" = -1 THEN NULL ELSE t15."plasterUnpaint"::TEXT || '. ' || c_materials_plasterunpaint."description" END AS "plasterUnpaint",
    CASE WHEN t15."plasterPaint" = -1 THEN NULL ELSE t15."plasterPaint"::TEXT || '. ' || c_materials_plasterpaint."description" END AS "plasterPaint",
    CASE WHEN t15."burntClay" = -1 THEN NULL ELSE t15."burntClay"::TEXT || '. ' || c_materials_burntclay."description" END AS "burntClay",
    NULLIF(t15."almena", -1) AS "almena",
    CASE WHEN t15."burnedStruct" = -1 THEN NULL ELSE t15."burnedStruct"::TEXT || '. ' || c_burnedstruct."description" END AS "burnedStruct",
    CASE WHEN t15."floors" = -1 THEN NULL ELSE t15."floors"::TEXT || '. ' || c_archfeatures."description" END AS "floors",
    CASE WHEN t15."walls" = -1 THEN NULL ELSE t15."walls"::TEXT || '. ' || c_archfeatures_walls."description" END AS "walls",
    CASE WHEN t15."drains" = -1 THEN NULL ELSE t15."drains"::TEXT || '. ' || c_archfeatures_drains."description" END AS "drainSitu",
    CASE WHEN t15."wallFixtures" = -1 THEN NULL ELSE t15."wallFixtures"::TEXT || '. ' || c_archfeatures_wallfixtures."description" END AS "wallFixSitu",
    CASE WHEN t15."murals" = -1 THEN NULL ELSE t15."murals"::TEXT || '. ' || c_archfeatures_murals."description" END AS "murals",
    CASE WHEN t15."columns" = -1 THEN NULL ELSE t15."columns"::TEXT || '. ' || c_archfeatures_columns."description" END AS "columns",
    CASE WHEN t15."taludes" = -1 THEN NULL ELSE t15."taludes"::TEXT || '. ' || c_archfeatures_taludes."description" END AS "taludes",
    CASE WHEN t15."tableros" = -1 THEN NULL ELSE t15."tableros"::TEXT || '. ' || c_archfeatures_tableros."description" END AS "tableros",
    CASE WHEN t15."floorMaterial" = -1 THEN NULL ELSE t15."floorMaterial"::TEXT || '. ' || c_floormat."description" END AS "floorMaterial",
    CASE WHEN t15."wallCoreStone" = -1 THEN NULL ELSE t15."wallCoreStone"::TEXT || '. ' || c_wallcorestone."description" END AS "wallCoreStone",
    t15."wallCoreOthMat"::TEXT || '. ' || c_wallcoreother."description" AS "wallCoreOthMat",
    CASE WHEN t15."wallFacing" = -1 THEN NULL ELSE t15."wallFacing"::TEXT || '. ' || c_wallfacing."description" END AS "wallFacing",
    CASE WHEN t2."intrusiveSherd" = -1 THEN NULL ELSE t2."intrusiveSherd"::TEXT || '. ' || c_intrusivesherd."description" END AS "intrusiveSherd",
    NULLIF(t2."height", -1) AS "height",
    CASE WHEN t3."arch1PMic" = -1 THEN NULL ELSE t3."arch1PMic"::TEXT || '. ' || c_archinterpprim."description" END AS "arch1PMic",
    CASE WHEN t3."arch1McTl" = -1 THEN NULL ELSE t3."arch1McTl"::TEXT || '. ' || c_archinterpprim_mctl."description" END AS "arch1McTl",
    CASE WHEN t3."arch1XlMe" = -1 THEN NULL ELSE t3."arch1XlMe"::TEXT || '. ' || c_archinterpprim_xlme."description" END AS "arch1XlMe",
    CASE WHEN t3."arch1Oxto" = -1 THEN NULL ELSE t3."arch1Oxto"::TEXT || '. ' || c_archinterpprim_oxto."description" END AS "arch1Oxto",
    t3."arch2PMic"::TEXT || '. ' || c_archinterpaltern."description" AS "arch2PMic",
    t3."arch2McTl"::TEXT || '. ' || c_archinterpaltern_mctl."description" AS "arch2McTl",
    t3."arch2XlMe"::TEXT || '. ' || c_archinterpaltern_xlme."description" AS "arch2XlMe",
    t3."arch2Oxto"::TEXT || '. ' || c_archinterpaltern_oxto."description" AS "arch2Oxto",
    CASE WHEN t3."constructQual" = -1 THEN NULL ELSE t3."constructQual"::TEXT || '. ' || c_constructqual."description" END AS "constructQual",
    CASE WHEN t3."func1PMic" = -1 THEN NULL ELSE t3."func1PMic"::TEXT || '. ' || c_funcinterpprim."description" END AS "func1PMic",
    CASE WHEN t3."func1McTl" = -1 THEN NULL ELSE t3."func1McTl"::TEXT || '. ' || c_funcinterpprim_mctl."description" END AS "func1McTl",
    CASE WHEN t3."func1XlMe" = -1 THEN NULL ELSE t3."func1XlMe"::TEXT || '. ' || c_funcinterpprim_xlme."description" END AS "func1XlMe",
    CASE WHEN t3."func1Oxto" = -1 THEN NULL ELSE t3."func1Oxto"::TEXT || '. ' || c_funcinterpprim_oxto."description" END AS "func1Oxto",
    t3."func2PMic"::TEXT || '. ' || c_funcinterpaltern."description" AS "func2PMic",
    t3."func2McTl"::TEXT || '. ' || c_funcinterpaltern_mctl."description" AS "func2McTl",
    t3."func2XlMe"::TEXT || '. ' || c_funcinterpaltern_xlme."description" AS "func2XlMe",
    t3."func2Oxto"::TEXT || '. ' || c_funcinterpaltern_oxto."description" AS "func2Oxto",
    CASE WHEN t16."archInt1PaTz" = -1 THEN NULL ELSE t16."archInt1PaTz"::TEXT || '. ' || c_complexgenprim."description" END AS "Cmplx_archInt1PaTz",
    CASE WHEN t16."archInt1McTl" = -1 THEN NULL ELSE t16."archInt1McTl"::TEXT || '. ' || c_complexgenprim_mctl."description" END AS "Cmplx_archInt1McTl",
    CASE WHEN t16."archInt1XlMt" = -1 THEN NULL ELSE t16."archInt1XlMt"::TEXT || '. ' || c_complexgenprim_xlmt."description" END AS "Cmplx_archInt1XlMt",
    CASE WHEN t16."archInt2PaTz" = -1 THEN NULL ELSE t16."archInt2PaTz"::TEXT || '. ' || c_complexgenaltern."description" END AS "Cmplx_archInt2PaTz",
    CASE WHEN t16."archInt2McTl" = -1 THEN NULL ELSE t16."archInt2McTl"::TEXT || '. ' || c_complexgenaltern_mctl."description" END AS "Cmplx_archInt2McTl",
    CASE WHEN t16."archInt2XlMt" = -1 THEN NULL ELSE t16."archInt2XlMt"::TEXT || '. ' || c_complexgenaltern_xlmt."description" END AS "Cmplx_archInt2XlMt",
    t16."funcIntPaTz"::TEXT || '. ' || c_complexfunwhole."description" AS "Cmplx_funcIntPaTz",
    t16."funcIntMcTl"::TEXT || '. ' || c_complexfunwhole_mctl."description" AS "Cmplx_funcIntMcTl",
    t16."funcIntXlMt"::TEXT || '. ' || c_complexfunwhole_xlmt."description" AS "Cmplx_funcIntXlMt",
    t16."funcResPaTz"::TEXT || '. ' || c_complexfunres."description" AS "Cmplx_funcResPaTz",
    t16."funcResMcTl"::TEXT || '. ' || c_complexfunres_mctl."description" AS "Cmplx_funcResMcTl",
    t16."funcResXlMt"::TEXT || '. ' || c_complexfunres_xlmt."description" AS "Cmplx_funcResXlMt",
    CASE WHEN t16."funcTmpPaTz" = -1 THEN NULL ELSE t16."funcTmpPaTz"::TEXT || '. ' || c_complexfuntemp."description" END AS "Cmplx_funcTmpPaTz",
    CASE WHEN t16."funcTmpMcTl" = -1 THEN NULL ELSE t16."funcTmpMcTl"::TEXT || '. ' || c_complexfuntemp_mctl."description" END AS "Cmplx_funcTmpMcTl",
    CASE WHEN t16."funcTmpXlMt" = -1 THEN NULL ELSE t16."funcTmpXlMt"::TEXT || '. ' || c_complexfuntemp_xlmt."description" END AS "Cmplx_funcTmpXlMt",
    CASE WHEN t16."funcCivPaTz" = -1 THEN NULL ELSE t16."funcCivPaTz"::TEXT || '. ' || c_complexfuncivic."description" END AS "Cmplx_funcCivPaTz",
    CASE WHEN t16."funcCivMcTl" = -1 THEN NULL ELSE t16."funcCivMcTl"::TEXT || '. ' || c_complexfuncivic_mctl."description" END AS "Cmplx_funcCivMcTl",
    CASE WHEN t16."funcCivXlMt" = -1 THEN NULL ELSE t16."funcCivXlMt"::TEXT || '. ' || c_complexfuncivic_xlmt."description" END AS "Cmplx_funcCivXlMt",
    CASE WHEN t16."funcOthXlMt" = -1 THEN NULL ELSE t16."funcOthXlMt"::TEXT || '. ' || c_complexfunother."description" END AS "Cmplx_funcOthXlMt",
    NULLIF(t16."complexNum", -1) AS "Cmplx_Num",
    NULLIF(t16."complexUnit"::text, 'XXXX') AS "Cmplx_Unit",
    NULLIF(t10."macroComplexNum", -1) AS "MCmplx_Num",
    NULLIF(t10."macroComplexUnit"::text, 'XXXX') AS "MCmplx_Unit",
    CASE WHEN t10."presPaTz" = -1 THEN NULL ELSE t10."presPaTz"::TEXT || '. ' || c_mcomplexgen."description" END AS "MCmplx_presPaTz",
    CASE WHEN t10."presMcTl" = -1 THEN NULL ELSE t10."presMcTl"::TEXT || '. ' || c_mcomplexgen_mctl."description" END AS "MCmplx_presMcTl",
    CASE WHEN t10."presXlMt" = -1 THEN NULL ELSE t10."presXlMt"::TEXT || '. ' || c_mcomplexgen_xlmt."description" END AS "MCmplx_presXlMt",
    CASE WHEN t10."funcIntPaTz" = -1 THEN NULL ELSE t10."funcIntPaTz"::TEXT || '. ' || c_mcomplexfun."description" END AS "MCmplx_funcIntPaTz",
    CASE WHEN t10."funcIntMcTl" = -1 THEN NULL ELSE t10."funcIntMcTl"::TEXT || '. ' || c_mcomplexfun_mctl."description" END AS "MCmplx_funcIntMcTl",
    CASE WHEN t10."funcIntXlMt" = -1 THEN NULL ELSE t10."funcIntXlMt"::TEXT || '. ' || c_mcomplexfun_xlmt."description" END AS "MCmplx_funcIntXlMt",
    CASE WHEN t3."neighborhoodChar" = -1 THEN NULL ELSE t3."neighborhoodChar"::TEXT || '. ' || c_neighborhoodchar."description" END AS "neighborhoodChar",
    CASE WHEN t15."freeStandWall" = -1 THEN NULL ELSE t15."freeStandWall"::TEXT || '. ' || c_otherarchfeatures."description" END AS "freeStandWall",
    CASE WHEN t15."wells" = -1 THEN NULL ELSE t15."wells"::TEXT || '. ' || c_otherarchfeatures_wells."description" END AS "wells",
    CASE WHEN t15."jagueys" = -1 THEN NULL ELSE t15."jagueys"::TEXT || '. ' || c_otherarchfeatures_jagueys."description" END AS "jagueyArch",
    CASE WHEN t15."puestos" = -1 THEN NULL ELSE t15."puestos"::TEXT || '. ' || c_otherarchfeatures_puestos."description" END AS "puestos",
    CASE WHEN t9."milpa" = -1 THEN NULL ELSE t9."milpa"::TEXT || '. ' || c_vegetation."description" END AS "milpa",
    CASE WHEN t9."barley" = -1 THEN NULL ELSE t9."barley"::TEXT || '. ' || c_vegetation_barley."description" END AS "barley",
    CASE WHEN t9."beans" = -1 THEN NULL ELSE t9."beans"::TEXT || '. ' || c_vegetation_beans."description" END AS "beans",
    CASE WHEN t9."alfalfaCut" = -1 THEN NULL ELSE t9."alfalfaCut"::TEXT || '. ' || c_vegetation_alfalfacut."description" END AS "alfalfaCut",
    CASE WHEN t9."alfalfaUncut" = -1 THEN NULL ELSE t9."alfalfaUncut"::TEXT || '. ' || c_vegetation_alfalfauncut."description" END AS "alfalfaUncut",
    CASE WHEN t9."nopales" = -1 THEN NULL ELSE t9."nopales"::TEXT || '. ' || c_vegetation_nopales."description" END AS "nopales",
    CASE WHEN t9."magueys" = -1 THEN NULL ELSE t9."magueys"::TEXT || '. ' || c_vegetation_magueys."description" END AS "magueys",
    CASE WHEN t9."fallow" = -1 THEN NULL ELSE t9."fallow"::TEXT || '. ' || c_vegetation_fallow."description" END AS "fallow",
    CASE WHEN t9."uncultivate" = -1 THEN NULL ELSE t9."uncultivate"::TEXT || '. ' || c_vegetation_uncultivate."description" END AS "uncultivate",
    CASE WHEN t9."cropWater" = -1 THEN NULL ELSE t9."cropWater"::TEXT || '. ' || c_water."description" END AS "cropWater",
    CASE WHEN t9."plowing" = -1 THEN NULL ELSE t9."plowing"::TEXT || '. ' || c_plowing."description" END AS "plowing",
    CASE WHEN t9."pitCultivate" = -1 THEN NULL ELSE t9."pitCultivate"::TEXT || '. ' || c_altering_features."description" END AS "pitCultivate",
    CASE WHEN t9."pitLoot" = -1 THEN NULL ELSE t9."pitLoot"::TEXT || '. ' || c_altering_features_pitloot."description" END AS "pitLoot",
    CASE WHEN t9."archaeoExcRest" = -1 THEN NULL ELSE t9."archaeoExcRest"::TEXT || '. ' || c_altering_features_archaeoexcrest."description" END AS "archaeoExcRest",
    CASE WHEN t9."pitMisc" = -1 THEN NULL ELSE t9."pitMisc"::TEXT || '. ' || c_altering_features_pitmisc."description" END AS "pitMisc",
    CASE WHEN t9."quarrying" = -1 THEN NULL ELSE t9."quarrying"::TEXT || '. ' || c_altering_features_quarrying."description" END AS "quarrying",
    CASE WHEN t9."stoneClearing" = -1 THEN NULL ELSE t9."stoneClearing"::TEXT || '. ' || c_altering_features_stoneclearing."description" END AS "stoneClearing",
    CASE WHEN t9."landLeveling" = -1 THEN NULL ELSE t9."landLeveling"::TEXT || '. ' || c_altering_features_landleveling."description" END AS "landLeveling",
    CASE WHEN t9."terracing" = -1 THEN NULL ELSE t9."terracing"::TEXT || '. ' || c_altering_features_terracing."description" END AS "terracing",
    CASE WHEN t9."ditching" = -1 THEN NULL ELSE t9."ditching"::TEXT || '. ' || c_altering_features_ditching."description" END AS "ditching",
    CASE WHEN t9."roadOrRail" = -1 THEN NULL ELSE t9."roadOrRail"::TEXT || '. ' || c_altering_features_roadorrail."description" END AS "roadOrRail",
    CASE WHEN t9."recentWall" = -1 THEN NULL ELSE t9."recentWall"::TEXT || '. ' || c_altering_features_recentwall."description" END AS "recentWall",
    CASE WHEN t9."stoneRows" = -1 THEN NULL ELSE t9."stoneRows"::TEXT || '. ' || c_altering_features_stonerows."description" END AS "stoneRows",
    CASE WHEN t9."recentBuild" = -1 THEN NULL ELSE t9."recentBuild"::TEXT || '. ' || c_altering_features_recentbuild."description" END AS "recentBuild",
    CASE WHEN t9."dam" = -1 THEN NULL ELSE t9."dam"::TEXT || '. ' || c_altering_features_dam."description" END AS "dam",
    CASE WHEN t9."jaguey" = -1 THEN NULL ELSE t9."jaguey"::TEXT || '. ' || c_altering_features_jaguey."description" END AS "jagueyMod",
    CASE WHEN t9."erosion" = -1 THEN NULL ELSE t9."erosion"::TEXT || '. ' || c_altering_features_erosion."description" END AS "erosion",
    CASE WHEN t9."silting" = -1 THEN NULL ELSE t9."silting"::TEXT || '. ' || c_altering_features_silting."description" END AS "silting",
    CASE WHEN t9."siteAlteration" = -1 THEN NULL ELSE t9."siteAlteration"::TEXT || '. ' || c_overall_condition."description" END AS "siteAlteration",
    CASE WHEN t2."slope" = -1 THEN NULL ELSE t2."slope"::TEXT || '. ' || c_slope."description" END AS "slope",
    CASE WHEN t13."groundstoneField" = -1 THEN NULL ELSE t13."groundstoneField"::TEXT || '. ' || c_workshopfield."description" END AS "groundstoneField",
    CASE WHEN t13."obsidianField" = -1 THEN NULL ELSE t13."obsidianField"::TEXT || '. ' || c_workshopfield_obsidian."description" END AS "obsidianField",
    NULLIF(t6."manos", -1) AS "manos",
    NULLIF(t6."metates", -1) AS "metates",
    NULLIF(t6."mortars", -1) AS "mortars",
    NULLIF(t6."pestles", -1) AS "pestles",
    NULLIF(t6."plasterSmoothers", -1) AS "plasterSmoothers",
    NULLIF(t6."plumbBobs", -1) AS "plumbBobs",
    NULLIF(t6."wallFixtures", -1) AS "wallFixSurf",
    NULLIF(t6."fireGods", -1) AS "fireGods",
    NULLIF(t6."sculptureFrags", -1) AS "sculptureFrags",
    NULLIF(t6."hammerStones", -1) AS "hammerStones",
    NULLIF(t6."slingStones", -1) AS "slingStones",
    NULLIF(t6."smoothStones", -1) AS "smoothStones",
    NULLIF(t6."whetStones", -1) AS "whetStones",
    NULLIF(t6."palettes", -1) AS "palettes",
    NULLIF(t6."celts", -1) AS "celts",
    NULLIF(t6."lajasReworked", -1) AS "lajasReworked",
    NULLIF(t6."anvils", -1) AS "anvils",
    NULLIF(t6."drains", -1) AS "drainSurf",
    NULLIF(t6."drainCovers", -1) AS "drainCovers",
    NULLIF(t6."groundstoneOther", -1) AS "groundstoneOther",
    NULLIF(t5."obsidianTot", -1) AS "obsidianTot",
    NULLIF(t5."obsidianBlades", -1) AS "obsidianBlades",
    NULLIF(t5."obsidianWaste", -1) AS "obsidianWaste",
    NULLIF(t5."obsidianScrapers", -1) AS "obsidianScrapers",
    NULLIF(t5."obsidianPoints", -1) AS "obsidianPoints",
    NULLIF(t5."obsidianCores", -1) AS "obsidianCores",
    NULLIF(t5."obsidianKnives", -1) AS "obsidianKnives",
    NULLIF(t5."obsidianEccentrics", -1) AS "obsidianEccentrics",
    NULLIF(t5."obsidianMagueyS", -1) AS "obsidianMagueyS",
    NULLIF(t5."obsidianUtFlake", -1) AS "obsidianUtFlake",
    NULLIF(t5."obsidianNodules", -1) AS "obsidianNodules",
    NULLIF(t5."basaltTot", -1) AS "basaltTot",
    NULLIF(t5."basaltTools", -1) AS "basaltTools",
    NULLIF(t5."chert", -1) AS "chert",
    NULLIF(t5."quartz", -1) AS "quartz",
    NULLIF(t6."slateTot", -1) AS "slateTot",
    NULLIF(t6."slatePainted", -1) AS "slatePainted",
    NULLIF(t6."alabaster", -1) AS "alabaster",
    NULLIF(t6."serpentine", -1) AS "serpentine",
    NULLIF(t6."jade", -1) AS "jade",
    NULLIF(t14."workedBone", -1) AS "workedBone",
    NULLIF(t14."shellTot", -1) AS "shellTot",
    NULLIF(t14."shellWorked", -1) AS "shellWorked",
    NULLIF(t17."figTot", -1) AS "figTot",
    NULLIF(t17."figHead", -1) AS "figHead",
    NULLIF(t17."figPPat", -1) AS "figPPat",
    NULLIF(t17."figPatl", -1) AS "figPatl",
    NULLIF(t17."figTzac", -1) AS "figTzac",
    NULLIF(t17."figMicc", -1) AS "figMicc",
    NULLIF(t17."figTlam", -1) AS "figTlam",
    NULLIF(t17."figXola", -1) AS "figXola",
    NULLIF(t17."figMete", -1) AS "figMete",
    NULLIF(t17."figTolt", -1) AS "figTolt",
    NULLIF(t17."figAzte", -1) AS "figAzte",
    NULLIF(t17."figPupp", -1) AS "figPupp",
    NULLIF(t17."spindleWhorl", -1) AS "spindleWhorl",
    NULLIF(t17."sealStamp", -1) AS "sealStamp",
    NULLIF(t17."earSpool", -1) AS "earSpool",
    NULLIF(t17."whistle", -1) AS "whistle",
    NULLIF(t17."flute", -1) AS "flute",
    COALESCE(t12."labAnalysts_Millon_R", FALSE) AS "labAnalysts_Millon_R",
    COALESCE(t12."labAnalysts_Drewitt_B", FALSE) AS "labAnalysts_Drewitt_B",
    COALESCE(t12."labAnalysts_Bennyhoff", FALSE) AS "labAnalysts_Bennyhoff",
    COALESCE(t12."labAnalysts_Banos", FALSE) AS "labAnalysts_Banos",
    COALESCE(t12."labAnalysts_Cowgill", FALSE) AS "labAnalysts_Cowgill",
    COALESCE(t12."labAnalysts_Spence", FALSE) AS "labAnalysts_Spence",
    COALESCE(t12."labAnalysts_Wallrath", FALSE) AS "labAnalysts_Wallrath",
    COALESCE(t12."labAnalysts_Marino", FALSE) AS "labAnalysts_Marino",
    COALESCE(t12."labAnalysts_Barbour", FALSE) AS "labAnalysts_Barbour",
    COALESCE(t12."labAnalysts_deLucio_A", FALSE) AS "labAnalysts_deLucio_A",
    COALESCE(t12."labAnalysts_deLucio_J", FALSE) AS "labAnalysts_deLucio_J",
    COALESCE(t12."labAnalysts_Blucher", FALSE) AS "labAnalysts_Blucher",
    COALESCE(t12."labAnalysts_Hungerford", FALSE) AS "labAnalysts_Hungerford",
    COALESCE(t12."labAnalysts_Sutherland", FALSE) AS "labAnalysts_Sutherland",
    COALESCE(t12."labAnalysts_Wilkerson", FALSE) AS "labAnalysts_Wilkerson",
    COALESCE(t12."labAnalysts_Sharnoff", FALSE) AS "labAnalysts_Sharnoff",
    COALESCE(t12."labAnalysts_Sanchez", FALSE) AS "labAnalysts_Sanchez",
    COALESCE(t12."labAnalysts_Fletcher", FALSE) AS "labAnalysts_Fletcher",
    COALESCE(t12."labAnalysts_Kolb", FALSE) AS "labAnalysts_Kolb",
    COALESCE(t12."labAnalysts_Drewitt_W", FALSE) AS "labAnalysts_Drewitt_W",
    COALESCE(t12."labAnalysts_Quisenberry", FALSE) AS "labAnalysts_Quisenberry",
    COALESCE(t12."labAnalysts_West_M", FALSE) AS "labAnalysts_West_M",
    COALESCE(t12."labAnalysts_Duran", FALSE) AS "labAnalysts_Duran",
    COALESCE(t12."labAnalysts_West_E", FALSE) AS "labAnalysts_West_E",
    NULLIF(t4."analysisYear", -1) AS "analysisYear",
    CASE WHEN t4."analysisQuarter" = -1 THEN NULL ELSE t4."analysisQuarter"::TEXT || '. ' || c_quarter_analysis."description" END AS "analysisQuarter",
    CASE WHEN t13."ceramicField" = -1 THEN NULL ELSE t13."ceramicField"::TEXT || '. ' || c_workshopfield_ceramic."description" END AS "ceramicField",
    CASE WHEN t2."ceramicAbundance" = -1 THEN NULL ELSE t2."ceramicAbundance"::TEXT || '. ' || c_ceramicabundance."description" END AS "ceramicAbundance",
    NULLIF(t17."candTot", -1) AS "candTot",
    NULLIF(t17."candCoat", -1) AS "candCoat",
    NULLIF(t17."candAtoy", -1) AS "candAtoy",
    NULLIF(t17."candEXol", -1) AS "candEXol",
    NULLIF(t17."candLXol", -1) AS "candLXol",
    NULLIF(t17."candMete", -1) AS "candMete",
    NULLIF(t17."candComm", -1) AS "candComm",
    NULLIF(t7."burner3P", -1) AS "burner3P",
    NULLIF(t7."coverHandled", -1) AS "coverHandled",
    NULLIF(t2."areaSite", -1) AS "areaSite",
    NULLIF(t8."totAll", -1) AS "totAll",
    NULLIF(t8."totPrec", -1) AS "totPrec",
    NULLIF(t8."totCuan", -1) AS "totCuan",
    NULLIF(t8."totTezo", -1) AS "totTezo",
    NULLIF(t8."totPatl", -1) AS "totPatl",
    NULLIF(t8."totTzac", -1) AS "totTzac",
    NULLIF(t8."totMicc", -1) AS "totMicc",
    NULLIF(t8."totTlam", -1) AS "totTlam",
    NULLIF(t8."totXola", -1) AS "totXola",
    NULLIF(t8."totMete", -1) AS "totMete",
    NULLIF(t8."totOxto", -1) AS "totOxto",
    NULLIF(t8."totXome", -1) AS "totXome",
    NULLIF(t8."totMaza", -1) AS "totMaza",
    NULLIF(t8."totAzte", -1) AS "totAzte",
    NULLIF(t7."censerTot", -1) AS "censerTot",
    NULLIF(t7."censerPPat", -1) AS "censerPPat",
    NULLIF(t7."censerPatl", -1) AS "censerPatl",
    NULLIF(t7."censerTzac", -1) AS "censerTzac",
    NULLIF(t7."censerMicc", -1) AS "censerMicc",
    NULLIF(t7."censerTlam", -1) AS "censerTlam",
    NULLIF(t7."censerXola", -1) AS "censerXola",
    NULLIF(t7."censerMete", -1) AS "censerMete",
    NULLIF(t7."censerOxto", -1) AS "censerOxto",
    NULLIF(t7."censerXome", -1) AS "censerXome",
    NULLIF(t7."censerMaza", -1) AS "censerMaza",
    NULLIF(t7."censerAzte", -1) AS "censerAzte",
    NULLIF(t7."toTot", -1) AS "toTot",
    NULLIF(t7."toRegular", -1) AS "toRegular",
    NULLIF(t7."toCoarse", -1) AS "toCoarse",
    NULLIF(t7."smoTot", -1) AS "smoTot",
    NULLIF(t7."smoTlam", -1) AS "smoTlam",
    NULLIF(t7."smoXola", -1) AS "smoXola",
    NULLIF(t7."smoMete", -1) AS "smoMete",
    NULLIF(t7."ollaTot", -1) AS "ollaTot",
    NULLIF(t7."ollaPatl", -1) AS "ollaPatl",
    NULLIF(t7."ollaWedge", -1) AS "ollaWedge",
    NULLIF(t7."ollaMicc", -1) AS "ollaMicc",
    NULLIF(t7."ollaTlam", -1) AS "ollaTlam",
    NULLIF(t7."ollaXola", -1) AS "ollaXola",
    NULLIF(t7."ollaMete", -1) AS "ollaMete",
    NULLIF(t7."comalTot", -1) AS "comalTot",
    NULLIF(t7."comalPatl", -1) AS "comalPatl",
    NULLIF(t7."comalTzac", -1) AS "comalTzac",
    NULLIF(t7."comalMicc", -1) AS "comalMicc",
    NULLIF(t7."comalTlam", -1) AS "comalTlam",
    NULLIF(t7."comalXola", -1) AS "comalXola",
    NULLIF(t7."comalMete", -1) AS "comalMete",
    NULLIF(t7."comalOxto", -1) AS "comalOxto",
    NULLIF(t7."comalPOxt", -1) AS "comalPOxt",
    NULLIF(t7."nubbinTot", -1) AS "nubbinTot",
    NULLIF(t7."nubbinPatl", -1) AS "nubbinPatl",
    NULLIF(t7."nubbinApet", -1) AS "nubbinApet",
    NULLIF(t7."nubbinInset", -1) AS "nubbinInset",
    NULLIF(t7."nubbinFlush", -1) AS "nubbinFlush",
    NULLIF(t7."nubbinAtoy", -1) AS "nubbinAtoy",
    NULLIF(t7."nubbinXola", -1) AS "nubbinXola",
    NULLIF(t7."nubbinMete", -1) AS "nubbinMete",
    NULLIF(t7."shrdStamped", -1) AS "shrdStamped",
    NULLIF(t7."shrdPlanoR", -1) AS "shrdPlanoR",
    NULLIF(t7."shrdStucco", -1) AS "shrdStucco",
    NULLIF(t7."shrdIncised", -1) AS "shrdIncised",
    NULLIF(t7."foreignTot", -1) AS "foreignTot",
    NULLIF(t7."mayaLow", -1) AS "mayaLow",
    NULLIF(t7."mayaHigh", -1) AS "mayaHigh",
    NULLIF(t7."huastec", -1) AS "huastec",
    NULLIF(t7."tajin", -1) AS "tajin",
    NULLIF(t7."gulfCoast", -1) AS "gulfCoast",
    NULLIF(t7."monteAlban", -1) AS "monteAlban",
    NULLIF(t7."oaxaca", -1) AS "oaxaca",
    NULLIF(t7."foreignOther", -1) AS "foreignOther",
    NULLIF(t7."adornos", -1) AS "adornos",
    NULLIF(t7."minatures", -1) AS "minatures",
    NULLIF(t7."copas", -1) AS "copas",
    NULLIF(t7."matteWare", -1) AS "matteWare",
    NULLIF(t7."granTot", -1) AS "granTot",
    NULLIF(t7."granPMic", -1) AS "granPMic",
    NULLIF(t7."granMicc", -1) AS "granMicc",
    NULLIF(t7."granTlam", -1) AS "granTlam",
    NULLIF(t7."granXola", -1) AS "granXola",
    NULLIF(t7."granMete", -1) AS "granMete",
    NULLIF(t17."ceramicDisk", -1) AS "ceramicDisk",
    CASE WHEN t13."obsidianSpencePhase1" = -1 THEN NULL ELSE t13."obsidianSpencePhase1"::TEXT || '. ' || c_workshopspence1."description" END AS "obsidianSpencePhase1",
    CASE WHEN t13."obsidianSpencePhase2" = -1 THEN NULL ELSE t13."obsidianSpencePhase2"::TEXT || '. ' || c_workshopspence2."description" END AS "obsidianSpencePhase2",
    CASE WHEN t13."ceramicKrotser" = -1 THEN NULL ELSE t13."ceramicKrotser"::TEXT || '. ' || c_workshopkrotser."description" END AS "ceramicKrotser",
    CASE WHEN t13."figurineConcBarbour" = -1 THEN NULL ELSE t13."figurineConcBarbour"::TEXT || '. ' || c_figurineconcbarbour."description" END AS "figurineConcBarbour",
    NULLIF(t2."areaStruct", -1) AS "areaStruct",
    NULLIF(t3."insubstantialCount", -1) AS "insubstantialCount",
    CASE WHEN t3."boundInfoQual" = -1 THEN NULL ELSE t3."boundInfoQual"::TEXT || '. ' || c_boundinfoqual."description" END AS "boundInfoQual"
FROM
    tmp_df9."location" AS t1
LEFT JOIN tmp_df9."description" AS t2 ON t1."SSN" = t2."SSN"
LEFT JOIN tmp_df9."archInterp" AS t3 ON t1."SSN" = t3."SSN"
LEFT JOIN tmp_df9."admin" AS t4 ON t1."SSN" = t4."SSN"
LEFT JOIN tmp_df9."lithicFlaked" AS t5 ON t1."SSN" = t5."SSN"
LEFT JOIN tmp_df9."lithicGround" AS t6 ON t1."SSN" = t6."SSN"
LEFT JOIN tmp_df9."cerVessel" AS t7 ON t1."SSN" = t7."SSN"
LEFT JOIN tmp_df9."cerPhTot" AS t8 ON t1."SSN" = t8."SSN"
LEFT JOIN tmp_df9."condition" AS t9 ON t1."SSN" = t9."SSN"
LEFT JOIN tmp_df9."complexMacroData" AS t10 ON t1."SSN" = t10."SSN"
LEFT JOIN "pivoted_fieldWorkers" AS t11 ON t1."SSN" = t11."SSN"
LEFT JOIN "pivoted_labAnalysts" AS t12 ON t1."SSN" = t12."SSN"
LEFT JOIN tmp_df9."workshop" AS t13 ON t1."SSN" = t13."SSN"
LEFT JOIN tmp_df9."artifactOther" AS t14 ON t1."SSN" = t14."SSN"
LEFT JOIN tmp_df9."archMaterial" AS t15 ON t1."SSN" = t15."SSN"
LEFT JOIN tmp_df9."complexData" AS t16 ON t1."SSN" = t16."SSN"
LEFT JOIN tmp_df9."cerNonVessel" AS t17 ON t1."SSN" = t17."SSN"
LEFT JOIN tmp_df9."Plazas" AS t18 ON t1."SSN" = t18."SSN"
-- Joins for Code-to-Text lookup tables
LEFT JOIN tmp_df9."Codes_quarter" AS c_quarter ON t4."collectionQuarter" = c_quarter."code"
LEFT JOIN tmp_df9."Codes_quarter" AS c_quarter_analysis ON t4."analysisQuarter" = c_quarter_analysis."code"
LEFT JOIN tmp_df9."Codes_lastBuildPhase" AS c_lastbuildphase ON t2."lastBuildPhase" = c_lastbuildphase."code"
LEFT JOIN tmp_df9."Codes_burials" AS c_burials ON t2."burials" = c_burials."code"
LEFT JOIN tmp_df9."Codes_midden" AS c_midden ON t2."midden" = c_midden."code"
LEFT JOIN tmp_df9."Codes_stoneQuant" AS c_stonequant ON t15."stoneQuant" = c_stonequant."code"
LEFT JOIN tmp_df9."Codes_stoneDist" AS c_stonedist ON t15."stoneDist" = c_stonedist."code"
LEFT JOIN tmp_df9."Codes_materials" AS c_materials ON t15."stoneCut" = c_materials."code"
LEFT JOIN tmp_df9."Codes_materials" AS c_materials_lajas ON t15."lajas" = c_materials_lajas."code"
LEFT JOIN tmp_df9."Codes_materials" AS c_materials_tepetate ON t15."tepetate" = c_materials_tepetate."code"
LEFT JOIN tmp_df9."Codes_materials" AS c_materials_adobe ON t15."adobe" = c_materials_adobe."code"
LEFT JOIN tmp_df9."Codes_materials" AS c_materials_xalnene ON t15."xalnene" = c_materials_xalnene."code"
LEFT JOIN tmp_df9."Codes_materials" AS c_materials_cascajo ON t15."cascajo" = c_materials_cascajo."code"
LEFT JOIN tmp_df9."Codes_materials" AS c_materials_concrete ON t15."concrete" = c_materials_concrete."code"
LEFT JOIN tmp_df9."Codes_materials" AS c_materials_plasterunpaint ON t15."plasterUnpaint" = c_materials_plasterunpaint."code"
LEFT JOIN tmp_df9."Codes_materials" AS c_materials_plasterpaint ON t15."plasterPaint" = c_materials_plasterpaint."code"
LEFT JOIN tmp_df9."Codes_materials" AS c_materials_burntclay ON t15."burntClay" = c_materials_burntclay."code"
LEFT JOIN tmp_df9."Codes_burnedStruct" AS c_burnedstruct ON t15."burnedStruct" = c_burnedstruct."code"
LEFT JOIN tmp_df9."Codes_archFeatures" AS c_archfeatures ON t15."floors" = c_archfeatures."code"
LEFT JOIN tmp_df9."Codes_archFeatures" AS c_archfeatures_walls ON t15."walls" = c_archfeatures_walls."code"
LEFT JOIN tmp_df9."Codes_archFeatures" AS c_archfeatures_drains ON t15."drains" = c_archfeatures_drains."code"
LEFT JOIN tmp_df9."Codes_archFeatures" AS c_archfeatures_wallfixtures ON t15."wallFixtures" = c_archfeatures_wallfixtures."code"
LEFT JOIN tmp_df9."Codes_archFeatures" AS c_archfeatures_murals ON t15."murals" = c_archfeatures_murals."code"
LEFT JOIN tmp_df9."Codes_archFeatures" AS c_archfeatures_columns ON t15."columns" = c_archfeatures_columns."code"
LEFT JOIN tmp_df9."Codes_archFeatures" AS c_archfeatures_taludes ON t15."taludes" = c_archfeatures_taludes."code"
LEFT JOIN tmp_df9."Codes_archFeatures" AS c_archfeatures_tableros ON t15."tableros" = c_archfeatures_tableros."code"
LEFT JOIN tmp_df9."Codes_FloorMat" AS c_floormat ON t15."floorMaterial" = c_floormat."code"
LEFT JOIN tmp_df9."Codes_wallCoreStone" AS c_wallcorestone ON t15."wallCoreStone" = c_wallcorestone."code"
LEFT JOIN tmp_df9."Codes_wallCoreOther" AS c_wallcoreother ON t15."wallCoreOthMat" = c_wallcoreother."code"
LEFT JOIN tmp_df9."Codes_wallFacing" AS c_wallfacing ON t15."wallFacing" = c_wallfacing."code"
LEFT JOIN tmp_df9."Codes_intrusiveSherd" AS c_intrusivesherd ON t2."intrusiveSherd" = c_intrusivesherd."code"
LEFT JOIN tmp_df9."Codes_ArchInterpPrim" AS c_archinterpprim ON t3."arch1PMic" = c_archinterpprim."code"
LEFT JOIN tmp_df9."Codes_ArchInterpPrim" AS c_archinterpprim_mctl ON t3."arch1McTl" = c_archinterpprim_mctl."code"
LEFT JOIN tmp_df9."Codes_ArchInterpPrim" AS c_archinterpprim_xlme ON t3."arch1XlMe" = c_archinterpprim_xlme."code"
LEFT JOIN tmp_df9."Codes_ArchInterpPrim" AS c_archinterpprim_oxto ON t3."arch1Oxto" = c_archinterpprim_oxto."code"
LEFT JOIN tmp_df9."Codes_ArchInterpAltern" AS c_archinterpaltern ON t3."arch2PMic" = c_archinterpaltern."code"
LEFT JOIN tmp_df9."Codes_ArchInterpAltern" AS c_archinterpaltern_mctl ON t3."arch2McTl" = c_archinterpaltern_mctl."code"
LEFT JOIN tmp_df9."Codes_ArchInterpAltern" AS c_archinterpaltern_xlme ON t3."arch2XlMe" = c_archinterpaltern_xlme."code"
LEFT JOIN tmp_df9."Codes_ArchInterpAltern" AS c_archinterpaltern_oxto ON t3."arch2Oxto" = c_archinterpaltern_oxto."code"
LEFT JOIN tmp_df9."Codes_ConstructQual" AS c_constructqual ON t3."constructQual" = c_constructqual."code"
LEFT JOIN tmp_df9."Codes_FuncInterpPrim" AS c_funcinterpprim ON t3."func1PMic" = c_funcinterpprim."code"
LEFT JOIN tmp_df9."Codes_FuncInterpPrim" AS c_funcinterpprim_mctl ON t3."func1McTl" = c_funcinterpprim_mctl."code"
LEFT JOIN tmp_df9."Codes_FuncInterpPrim" AS c_funcinterpprim_xlme ON t3."func1XlMe" = c_funcinterpprim_xlme."code"
LEFT JOIN tmp_df9."Codes_FuncInterpPrim" AS c_funcinterpprim_oxto ON t3."func1Oxto" = c_funcinterpprim_oxto."code"
LEFT JOIN tmp_df9."Codes_FuncInterpAltern" AS c_funcinterpaltern ON t3."func2PMic" = c_funcinterpaltern."code"
LEFT JOIN tmp_df9."Codes_FuncInterpAltern" AS c_funcinterpaltern_mctl ON t3."func2McTl" = c_funcinterpaltern_mctl."code"
LEFT JOIN tmp_df9."Codes_FuncInterpAltern" AS c_funcinterpaltern_xlme ON t3."func2XlMe" = c_funcinterpaltern_xlme."code"
LEFT JOIN tmp_df9."Codes_FuncInterpAltern" AS c_funcinterpaltern_oxto ON t3."func2Oxto" = c_funcinterpaltern_oxto."code"
LEFT JOIN tmp_df9."Codes_complexGenPrim" AS c_complexgenprim ON t16."archInt1PaTz" = c_complexgenprim."code"
LEFT JOIN tmp_df9."Codes_complexGenPrim" AS c_complexgenprim_mctl ON t16."archInt1McTl" = c_complexgenprim_mctl."code"
LEFT JOIN tmp_df9."Codes_complexGenPrim" AS c_complexgenprim_xlmt ON t16."archInt1XlMt" = c_complexgenprim_xlmt."code"
LEFT JOIN tmp_df9."Codes_complexGenAltern" AS c_complexgenaltern ON t16."archInt2PaTz" = c_complexgenaltern."code"
LEFT JOIN tmp_df9."Codes_complexGenAltern" AS c_complexgenaltern_mctl ON t16."archInt2McTl" = c_complexgenaltern_mctl."code"
LEFT JOIN tmp_df9."Codes_complexGenAltern" AS c_complexgenaltern_xlmt ON t16."archInt2XlMt" = c_complexgenaltern_xlmt."code"
LEFT JOIN tmp_df9."Codes_complexFunWhole" AS c_complexfunwhole ON t16."funcIntPaTz" = c_complexfunwhole."code"
LEFT JOIN tmp_df9."Codes_complexFunWhole" AS c_complexfunwhole_mctl ON t16."funcIntMcTl" = c_complexfunwhole_mctl."code"
LEFT JOIN tmp_df9."Codes_complexFunWhole" AS c_complexfunwhole_xlmt ON t16."funcIntXlMt" = c_complexfunwhole_xlmt."code"
LEFT JOIN tmp_df9."Codes_complexFunRes" AS c_complexfunres ON t16."funcResPaTz" = c_complexfunres."code"
LEFT JOIN tmp_df9."Codes_complexFunRes" AS c_complexfunres_mctl ON t16."funcResMcTl" = c_complexfunres_mctl."code"
LEFT JOIN tmp_df9."Codes_complexFunRes" AS c_complexfunres_xlmt ON t16."funcResXlMt" = c_complexfunres_xlmt."code"
LEFT JOIN tmp_df9."Codes_complexFunTemp" AS c_complexfuntemp ON t16."funcTmpPaTz" = c_complexfuntemp."code"
LEFT JOIN tmp_df9."Codes_complexFunTemp" AS c_complexfuntemp_mctl ON t16."funcTmpMcTl" = c_complexfuntemp_mctl."code"
LEFT JOIN tmp_df9."Codes_complexFunTemp" AS c_complexfuntemp_xlmt ON t16."funcTmpXlMt" = c_complexfuntemp_xlmt."code"
LEFT JOIN tmp_df9."Codes_complexFunCivic" AS c_complexfuncivic ON t16."funcCivPaTz" = c_complexfuncivic."code"
LEFT JOIN tmp_df9."Codes_complexFunCivic" AS c_complexfuncivic_mctl ON t16."funcCivMcTl" = c_complexfuncivic_mctl."code"
LEFT JOIN tmp_df9."Codes_complexFunCivic" AS c_complexfuncivic_xlmt ON t16."funcCivXlMt" = c_complexfuncivic_xlmt."code"
LEFT JOIN tmp_df9."Codes_complexFunOther" AS c_complexfunother ON t16."funcOthXlMt" = c_complexfunother."code"
LEFT JOIN tmp_df9."Codes_McomplexGen" AS c_mcomplexgen ON t10."presPaTz" = c_mcomplexgen."code"
LEFT JOIN tmp_df9."Codes_McomplexGen" AS c_mcomplexgen_mctl ON t10."presMcTl" = c_mcomplexgen_mctl."code"
LEFT JOIN tmp_df9."Codes_McomplexGen" AS c_mcomplexgen_xlmt ON t10."presXlMt" = c_mcomplexgen_xlmt."code"
LEFT JOIN tmp_df9."Codes_McomplexFun" AS c_mcomplexfun ON t10."funcIntPaTz" = c_mcomplexfun."code"
LEFT JOIN tmp_df9."Codes_McomplexFun" AS c_mcomplexfun_mctl ON t10."funcIntMcTl" = c_mcomplexfun_mctl."code"
LEFT JOIN tmp_df9."Codes_McomplexFun" AS c_mcomplexfun_xlmt ON t10."funcIntXlMt" = c_mcomplexfun_xlmt."code"
LEFT JOIN tmp_df9."Codes_neighborhoodChar" AS c_neighborhoodchar ON t3."neighborhoodChar" = c_neighborhoodchar."code"
LEFT JOIN tmp_df9."Codes_otherArchFeatures" AS c_otherarchfeatures ON t15."freeStandWall" = c_otherarchfeatures."code"
LEFT JOIN tmp_df9."Codes_otherArchFeatures" AS c_otherarchfeatures_wells ON t15."wells" = c_otherarchfeatures_wells."code"
LEFT JOIN tmp_df9."Codes_otherArchFeatures" AS c_otherarchfeatures_jagueys ON t15."jagueys" = c_otherarchfeatures_jagueys."code"
LEFT JOIN tmp_df9."Codes_otherArchFeatures" AS c_otherarchfeatures_puestos ON t15."puestos" = c_otherarchfeatures_puestos."code"
LEFT JOIN tmp_df9."Codes_vegetation" AS c_vegetation ON t9."milpa" = c_vegetation."code"
LEFT JOIN tmp_df9."Codes_vegetation" AS c_vegetation_barley ON t9."barley" = c_vegetation_barley."code"
LEFT JOIN tmp_df9."Codes_vegetation" AS c_vegetation_beans ON t9."beans" = c_vegetation_beans."code"
LEFT JOIN tmp_df9."Codes_vegetation" AS c_vegetation_alfalfacut ON t9."alfalfaCut" = c_vegetation_alfalfacut."code"
LEFT JOIN tmp_df9."Codes_vegetation" AS c_vegetation_alfalfauncut ON t9."alfalfaUncut" = c_vegetation_alfalfauncut."code"
LEFT JOIN tmp_df9."Codes_vegetation" AS c_vegetation_nopales ON t9."nopales" = c_vegetation_nopales."code"
LEFT JOIN tmp_df9."Codes_vegetation" AS c_vegetation_magueys ON t9."magueys" = c_vegetation_magueys."code"
LEFT JOIN tmp_df9."Codes_vegetation" AS c_vegetation_fallow ON t9."fallow" = c_vegetation_fallow."code"
LEFT JOIN tmp_df9."Codes_vegetation" AS c_vegetation_uncultivate ON t9."uncultivate" = c_vegetation_uncultivate."code"
LEFT JOIN tmp_df9."Codes_water" AS c_water ON t9."cropWater" = c_water."code"
LEFT JOIN tmp_df9."Codes_plowing" AS c_plowing ON t9."plowing" = c_plowing."code"
LEFT JOIN tmp_df9."Codes_altering_features" AS c_altering_features ON t9."pitCultivate" = c_altering_features."code"
LEFT JOIN tmp_df9."Codes_altering_features" AS c_altering_features_pitloot ON t9."pitLoot" = c_altering_features_pitloot."code"
LEFT JOIN tmp_df9."Codes_altering_features" AS c_altering_features_archaeoexcrest ON t9."archaeoExcRest" = c_altering_features_archaeoexcrest."code"
LEFT JOIN tmp_df9."Codes_altering_features" AS c_altering_features_pitmisc ON t9."pitMisc" = c_altering_features_pitmisc."code"
LEFT JOIN tmp_df9."Codes_altering_features" AS c_altering_features_quarrying ON t9."quarrying" = c_altering_features_quarrying."code"
LEFT JOIN tmp_df9."Codes_altering_features" AS c_altering_features_stoneclearing ON t9."stoneClearing" = c_altering_features_stoneclearing."code"
LEFT JOIN tmp_df9."Codes_altering_features" AS c_altering_features_landleveling ON t9."landLeveling" = c_altering_features_landleveling."code"
LEFT JOIN tmp_df9."Codes_altering_features" AS c_altering_features_terracing ON t9."terracing" = c_altering_features_terracing."code"
LEFT JOIN tmp_df9."Codes_altering_features" AS c_altering_features_ditching ON t9."ditching" = c_altering_features_ditching."code"
LEFT JOIN tmp_df9."Codes_altering_features" AS c_altering_features_roadorrail ON t9."roadOrRail" = c_altering_features_roadorrail."code"
LEFT JOIN tmp_df9."Codes_altering_features" AS c_altering_features_recentwall ON t9."recentWall" = c_altering_features_recentwall."code"
LEFT JOIN tmp_df9."Codes_altering_features" AS c_altering_features_stonerows ON t9."stoneRows" = c_altering_features_stonerows."code"
LEFT JOIN tmp_df9."Codes_altering_features" AS c_altering_features_recentbuild ON t9."recentBuild" = c_altering_features_recentbuild."code"
LEFT JOIN tmp_df9."Codes_altering_features" AS c_altering_features_dam ON t9."dam" = c_altering_features_dam."code"
LEFT JOIN tmp_df9."Codes_altering_features" AS c_altering_features_jaguey ON t9."jaguey" = c_altering_features_jaguey."code"
LEFT JOIN tmp_df9."Codes_altering_features" AS c_altering_features_erosion ON t9."erosion" = c_altering_features_erosion."code"
LEFT JOIN tmp_df9."Codes_altering_features" AS c_altering_features_silting ON t9."silting" = c_altering_features_silting."code"
LEFT JOIN tmp_df9."Codes_overall_condition" AS c_overall_condition ON t9."siteAlteration" = c_overall_condition."code"
LEFT JOIN tmp_df9."Codes_slope" AS c_slope ON t2."slope" = c_slope."code"
LEFT JOIN tmp_df9."Codes_workshopField" AS c_workshopfield ON t13."groundstoneField" = c_workshopfield."code"
LEFT JOIN tmp_df9."Codes_workshopField" AS c_workshopfield_obsidian ON t13."obsidianField" = c_workshopfield_obsidian."code"
LEFT JOIN tmp_df9."Codes_workshopField" AS c_workshopfield_ceramic ON t13."ceramicField" = c_workshopfield_ceramic."code"
LEFT JOIN tmp_df9."Codes_ceramicAbundance" AS c_ceramicabundance ON t2."ceramicAbundance" = c_ceramicabundance."code"
LEFT JOIN tmp_df9."Codes_workshopSpence1" AS c_workshopspence1 ON t13."obsidianSpencePhase1" = c_workshopspence1."code"
LEFT JOIN tmp_df9."Codes_workshopSpence2" AS c_workshopspence2 ON t13."obsidianSpencePhase2" = c_workshopspence2."code"
LEFT JOIN tmp_df9."Codes_workshopKrotser" AS c_workshopkrotser ON t13."ceramicKrotser" = c_workshopkrotser."code"
LEFT JOIN tmp_df9."Codes_figurineConcBarbour" AS c_figurineconcbarbour ON t13."figurineConcBarbour" = c_figurineconcbarbour."code"
LEFT JOIN tmp_df9."Codes_boundInfoQual" AS c_boundinfoqual ON t3."boundInfoQual" = c_boundinfoqual."code"
ORDER BY
    t1."SSN";