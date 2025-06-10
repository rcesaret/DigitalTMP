-- ============================================================================
--           Flattening Query for TMP_DF9 Benchmark Database
-- ============================================================================
-- This query joins the 18 core data tables from the tmp_df9 schema into a
-- single wide-format table. It uses LEFT JOINs from the central "tblSSN"
-- table to ensure all site records are preserved.
--
-- All columns are explicitly aliased to prevent name collisions and provide
-- clarity on the origin of each field in the final flattened table.
-- ============================================================================

SELECT
    t1."SSN",
    t1."Grid_N" AS "tblSSN_Grid_N",
    t1."Grid_E" AS "tblSSN_Grid_E",
    t1."YDS_Code" AS "tblSSN_YDS_Code",
    t1."Lab_YDS" AS "tblSSN_Lab_YDS",
    t1."Area" AS "tblSSN_Area",
    t1."Mound" AS "tblSSN_Mound",
    t1."Type" AS "tblSSN_Type",
    t1."Variety" AS "tblSSN_Variety",
    t1."Pre_TMP_Designation" AS "tblSSN_Pre_TMP_Designation",
    t1."Publication" AS "tblSSN_Publication",

    t2."Arch_Pres" AS "archaeology_Arch_Pres",
    t2."Arch_Conf" AS "archaeology_Arch_Conf",
    t2."Arch_Density" AS "archaeology_Arch_Density",
    t2."Arch_Notes" AS "archaeology_Arch_Notes",

    t3."Arch_Type" AS "architecture_Arch_Type",
    t3."Plat_Type" AS "architecture_Plat_Type",
    t3."Orient" AS "architecture_Orient",
    t3."Arch_Shape" AS "architecture_Arch_Shape",
    t3."Num_Stages" AS "architecture_Num_Stages",
    t3."Length" AS "architecture_Length",
    t3."Width" AS "architecture_Width",
    t3."Height" AS "architecture_Height",
    t3."Area_Basal" AS "architecture_Area_Basal",
    t3."TALUD" AS "architecture_TALUD",
    t3."TABLERO" AS "architecture_TABLERO",
    t3."Stairway" AS "architecture_Stairway",
    t3."Masonry_Type" AS "architecture_Masonry_Type",
    t3."Stucco_Pres" AS "architecture_Stucco_Pres",
    t3."Stucco_Color" AS "architecture_Stucco_Color",
    t3."Arch_Comments" AS "architecture_Arch_Comments",

    t4."Plaster_Floor_Present" AS "plasterFloor_Plaster_Floor_Present",
    t4."Plaster_Floor_Area" AS "plasterFloor_Plaster_Floor_Area",
    t4."Plaster_Floor_Thick" AS "plasterFloor_Plaster_Floor_Thick",
    t4."Plaster_Floor_Color" AS "plasterFloor_Plaster_Floor_Color",
    t4."Plaster_Floor_Hard" AS "plasterFloor_Plaster_Floor_Hard",
    t4."Plaster_Floor_Inclusions" AS "plasterFloor_Plaster_Floor_Inclusions",

    t5."Figurine_Type" AS "figurine_Figurine_Type",
    t5."Total_Count" AS "figurine_Total_Count",
    t5."Head_Count" AS "figurine_Head_Count",
    t5."Body_Count" AS "figurine_Body_Count",
    t5."Limb_Count" AS "figurine_Limb_Count",
    t5."Animal_Count" AS "figurine_Animal_Count",
    t5."Comments" AS "figurine_Comments",

    t6."Total_Fig_Obs" AS "figurineObsidian_Total_Fig_Obs",
    t6."Comments" AS "figurineObsidian_Comments",

    t7."Total" AS "archMaterial_Total",
    t7."Comments" AS "archMaterial_Comments",

    t8."Malacates" AS "artifactOther_Malacates",
    t8."Candeleros" AS "artifactOther_Candeleros",
    t8."Adornos" AS "artifactOther_Adornos",
    t8."Stand_Frags" AS "artifactOther_Stand_Frags",
    t8."Misc_Baked_Clay" AS "artifactOther_Misc_Baked_Clay",
    t8."Worked_Sherds" AS "artifactOther_Worked_Sherds",
    t8."Molds" AS "artifactOther_Molds",
    t8."Musical_Instr" AS "artifactOther_Musical_Instr",
    t8."Ocarinas" AS "artifactOther_Ocarinas",
    t8."Whistles" AS "artifactOther_Whistles",
    t8."Micas" AS "artifactOther_Micas",
    t8."Slates" AS "artifactOther_Slates",
    t8."Stucco" AS "artifactOther_Stucco",
    t8."Pigment" AS "artifactOther_Pigment",
    t8."Shell" AS "artifactOther_Shell",
    t8."Comments" AS "artifactOther_Comments",

    t9."Form" AS "cerNonVessel_Form",
    t9."Count" AS "cerNonVessel_Count",
    t9."Comments" AS "cerNonVessel_Comments",

    t10."Phase_Total_Code" AS "cerPhTot_Phase_Total_Code",

    t11."Form_Code" AS "cerVessel_Form_Code",
    t11."Ware_Code" AS "cerVessel_Ware_Code",
    t11."Type_Code" AS "cerVessel_Type_Code",
    t11."Variety_Code" AS "cerVessel_Variety_Code",
    t11."Count" AS "cerVessel_Count",

    t12."Data" AS "complexData_Data",
    t12."Comments" AS "complexData_Comments",

    t13."Data" AS "complexMacroData_Data",
    t13."Comments" AS "complexMacroData_Comments",

    t14."Site_Cond_Code" AS "condition_Site_Cond_Code",
    t14."Veg_Cond_Code" AS "condition_Veg_Cond_Code",
    t14."Collector_Bias_Code" AS "condition_Collector_Bias_Code",
    t14."Publication_Status" AS "condition_Publication_Status",
    t14."Notes" AS "condition_Notes",

    t15."Field_Wrkr_Code" AS "fieldWorkers_Field_Wrkr_Code",

    t16."Lab_Anlyst_Code" AS "labAnalysts_Lab_Anlyst_Code",

    t17."Obsidian_Type_Code" AS "lithicFlaked_Obsidian_Type_Code",
    t17."Core_Type_Code" AS "lithicFlaked_Core_Type_Code",
    t17."Blade_Type_Code" AS "lithicFlaked_Blade_Type_Code",
    t17."Flake_Type_Code" AS "lithicFlaked_Flake_Type_Code",
    t17."Biface_Type_Code" AS "lithicFlaked_Biface_Type_Code",
    t17."Projectile_Pt_Code" AS "lithicFlaked_Projectile_Pt_Code",
    t17."Scraper_Code" AS "lithicFlaked_Scraper_Code",
    t17."Debitage_Code" AS "lithicFlaked_Debitage_Code",
    t17."Comments" AS "lithicFlaked_Comments",

    t18."Material_Code" AS "lithicGround_Material_Code",
    t18."Type_Code" AS "lithicGround_Type_Code",
    t18."Portion_Code" AS "lithicGround_Portion_Code",
    t18."Comments" AS "lithicGround_Comments"

FROM
    tmp_df9."tblSSN" AS t1
LEFT JOIN tmp_df9."archaeology" AS t2 ON t1."SSN" = t2."SSN"
LEFT JOIN tmp_df9."architecture" AS t3 ON t1."SSN" = t3."SSN"
LEFT JOIN tmp_df9."plasterFloor" AS t4 ON t1."SSN" = t4."SSN"
LEFT JOIN tmp_df9."figurine" AS t5 ON t1."SSN" = t5."SSN"
LEFT JOIN tmp_df9."figurineObsidian" AS t6 ON t1."SSN" = t6."SSN"
LEFT JOIN tmp_df9."archMaterial" AS t7 ON t1."SSN" = t7."SSN"
LEFT JOIN tmp_df9."artifactOther" AS t8 ON t1."SSN" = t8."SSN"
LEFT JOIN tmp_df9."cerNonVessel" AS t9 ON t1."SSN" = t9."SSN"
LEFT JOIN tmp_df9."cerPhTot" AS t10 ON t1."SSN" = t10."SSN"
LEFT JOIN tmp_df9."cerVessel" AS t11 ON t1."SSN" = t11."SSN"
LEFT JOIN tmp_df9."complexData" AS t12 ON t1."SSN" = t12."SSN"
LEFT JOIN tmp_df9."complexMacroData" AS t13 ON t1."SSN" = t13."SSN"
LEFT JOIN tmp_df9."condition" AS t14 ON t1."SSN" = t14."SSN"
LEFT JOIN tmp_df9."fieldWorkers" AS t15 ON t1."SSN" = t15."SSN"
LEFT JOIN tmp_df9."labAnalysts" AS t16 ON t1."SSN" = t16."SSN"
LEFT JOIN tmp_df9."lithicFlaked" AS t17 ON t1."SSN" = t17."SSN"
LEFT JOIN tmp_df9."lithicGround" AS t18 ON t1."SSN" = t18."SSN";