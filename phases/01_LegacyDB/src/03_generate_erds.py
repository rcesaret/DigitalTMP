# -*- coding: utf-8 -*-
"""
Generates Entity-Relationship Diagrams (ERDs) for all target databases.

This script connects to each database specified in the configuration file,
reflects its schema, and generates one or more ERDs using SQLAlchemy and
Graphviz.

For all databases, a full ERD of the entire schema is generated.

For the highly complex 'TMP_DF9' database, this script also generates
additional, focused ERDs that visualize specific data subsystems (e.g.,
the ceramic data tables, the lithic data tables). This is a strategic
choice to create more readable and analytically useful diagrams than a single,
monolithic ERD.

The output is a set of SVG files saved to the `outputs/erds/` directory.

Prerequisites:
- The Graphviz command-line tool (e.g., `dot`) must be installed and
  available in the system's PATH.
- All target databases must exist on the PostgreSQL server.

Usage:
    From the src/ directory, run:
    $ python 03_generate_erds.py --config config.ini

"""

import argparse
import configparser
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy import MetaData, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.schema import Table
from sqlalchemy_schemadisplay import create_schema_graph

# --- Constants ---
LOG_FILE_NAME = "03_generate_erds.log"
OUTPUT_ERDS_DIR = "outputs/erds"

# Subsystem definitions for focused ERDs for the 'tmp_df9' schema.
# Each key is a subsystem name, and the value is a list of table names.
TMP_DF9_SUBSYSTEMS = {
    "Core_Data_Tables": [
        "location",
        "description",
        "archInterp",
        "admin",
        "lithicFlaked",
        "lithicGround",
        "cerVessel",
        "cerPhTot",
        "condition",
        "figurine",
        "plasterFloor",
        "archaeology",
        "artifactOther",
        "architecture",
        "cerNonVessel",
        "complexData",
        "complexMacroData",
    ],
    "Ceramic_System": [
        "cerVessel",
        "cerPhTot",
        "cerNonVessel",
        "Codes_Ware",
        "Codes_Ceramic_Variety",
        "Codes_Ceramic_Form",
        "Codes_Ceramic_Type",
        "Codes_Phase",
    ],
    "Lithic_System": [
        "lithicFlaked",
        "lithicGround",
        "Codes_Material",
        "Codes_Core_Type",
        "Codes_Biface_Type",
        "Codes_Blade_Type",
        "Codes_Flake_Type",
        "Codes_Projectile_Pt",
        "Codes_Scraper_Type",
    ],
}


# --- Setup Functions ---


def setup_logging(log_dir: Path) -> None:
    """Configures logging to both console and a file."""
    log_dir.mkdir(exist_ok=True)
    log_path = log_dir / LOG_FILE_NAME
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)-7s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_path, mode="w"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def parse_arguments() -> argparse.Namespace:
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate ERDs for all project databases."
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config.ini",
        help="Path to the configuration file (default: config.ini)",
    )
    return parser.parse_args()


def get_sqlalchemy_engine(db_config: Dict[str, Any], db_name: str) -> Engine | None:
    """Creates a SQLAlchemy engine, returning None on failure."""
    try:
        db_url = (
            f"postgresql+psycopg2://{db_config['user']}:{db_config['password']}"
            f"@{db_config['host']}:{db_config['port']}/{db_name}"
        )
        return create_engine(db_url)
    except Exception as e:
        logging.error(
            "Failed to create SQLAlchemy engine for '%s': %s",
            db_name,
            e,
        )
        return None


def get_schema_for_db(db_name: str, legacy_dbs: List[str]) -> str:
    """
    Determines the correct schema name for a given database name.

    Legacy databases use a schema named after the database, but in lowercase.
    Benchmark databases use the default 'public' schema.

    """
    return db_name.lower() if db_name in legacy_dbs else "public"


# --- Core Graphing Logic ---


def generate_and_save_erd(
    engine: Engine,
    metadata: MetaData,
    output_path: Path,
    tables_to_include: Optional[List[Table]] = None,
    graph_title: str = "",
) -> None:
    """
    Generates a single ERD using Graphviz and saves it as an SVG.

    Args:
        engine: The SQLAlchemy engine to connect to the database.
        metadata: The SQLAlchemy MetaData object containing reflected tables.
        output_path: The full path where the SVG file will be saved.
        tables_to_include: If provided, only these tables will be in the ERD.
                           If None, all tables in metadata are used.
        graph_title: A title to display on the generated graph.
    """
    logging.info(
        "Generating ERD for '%s' -> %s",
        graph_title,
        output_path.name,
    )
    # Ensure the output directory exists in case this function is used
    # independently of the main orchestrator which normally creates it.
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        # Graphviz attributes for improved readability
        graph = create_schema_graph(
            engine,
            metadata=metadata,
            tables=tables_to_include,
            show_datatypes=False,
            show_indexes=False,
            rankdir="LR",  # Left-to-Right layout
            concentrate=False,
        )
        # Set graph, node, and edge attributes using the pydot API
        graph.set_graph_defaults(label=graph_title, labelloc="t", fontsize="20")
        graph.set_node_defaults(fontname="Helvetica", fontsize="10")
        graph.set_edge_defaults(fontname="Helvetica", fontsize="8")
        graph.write_svg(str(output_path))
        logging.info("Successfully generated SVG.")
    except Exception as e:
        logging.error(
            "Failed to generate ERD for '%s'. Error: %s",
            graph_title,
            e,
            exc_info=True,
        )


# --- Main Orchestrator ---


def main() -> None:
    """Main function to orchestrate ERD generation for all databases."""
    args = parse_arguments()
    config_path = Path(args.config)

    log_dir = Path(__file__).parent
    setup_logging(log_dir)
    logging.info("--- Starting ERD Generation Pipeline ---")

    logging.info("Reading configuration from: %s", config_path)
    if not config_path.is_file():
        logging.critical("Configuration file not found: %s", config_path)
        sys.exit(1)

    config = configparser.ConfigParser()
    config.read(config_path)

    try:
        db_config_root = dict(config["postgresql"])
        legacy_dbs = [
            db.strip()
            for db in config.get("databases", "legacy_dbs").split(",")
            if db.strip()
        ]
        benchmark_dbs = [
            db.strip()
            for db in config.get("databases", "benchmark_dbs").split(",")
            if db.strip()
        ]
        all_dbs_to_profile = legacy_dbs + benchmark_dbs

        project_root = Path(__file__).parent.parent
        output_dir = project_root / OUTPUT_ERDS_DIR
        output_dir.mkdir(parents=True, exist_ok=True)

    except (configparser.NoSectionError, configparser.NoOptionError) as e:
        logging.critical(
            "Config file is missing a required section or option: %s",
            e,
        )
        sys.exit(1)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

    for i, db_name in enumerate(all_dbs_to_profile, 1):
        logging.info("=" * 80)
        logging.info(
            "Processing Database %s/%s: %s",
            i,
            len(all_dbs_to_profile),
            db_name,
        )
        logging.info("=" * 80)

        engine = get_sqlalchemy_engine(db_config_root, db_name)
        if not engine:
            logging.error(
                "Skipping ERD generation for '%s' due to connection failure.",
                db_name,
            )
            continue

        schema_name = get_schema_for_db(db_name, legacy_dbs)
        logging.info("Reflecting schema '%s'...", schema_name)
        metadata = MetaData()
        try:
            metadata.reflect(bind=engine, schema=schema_name)
        except Exception as e:
            logging.error(
                "Could not reflect schema '%s'. Skipping. Error: %s",
                schema_name,
                e,
            )
            continue

        # 1. Generate the full ERD for every database
        full_erd_path = output_dir / f"{db_name}_full_ERD_{timestamp}.svg"
        generate_and_save_erd(
            engine=engine,
            metadata=metadata,
            output_path=full_erd_path,
            graph_title=f"Full ERD for {db_name}",
        )

        # 2. For tmp_df9, generate additional focused ERDs
        #    Normalize the database name to handle case differences when
        #    reading from the config file.
        if db_name.upper() == "TMP_DF9":
            logging.info("Generating focused ERDs for '%s'...", db_name)
            for subsystem_name, table_list in TMP_DF9_SUBSYSTEMS.items():
                # Create a lowercase table list for case-insensitive matching
                lowercase_table_list = [t.lower() for t in table_list]
                # Filter the reflected tables to only those in our subsystem list
                tables_to_include = [
                    table
                    for name, table in metadata.tables.items()
                    if name.split(".")[-1].lower() in lowercase_table_list
                ]

                if not tables_to_include:
                    logging.warning(
                        f"No tables found for subsystem '{subsystem_name}'. Skipping."
                    )
                    continue

                focused_erd_path = (
                    output_dir / f"{db_name}_focused_{subsystem_name}_{timestamp}.svg"
                )
                generate_and_save_erd(
                    engine=engine,
                    metadata=metadata,
                    output_path=focused_erd_path,
                    tables_to_include=tables_to_include,
                    graph_title=f"{db_name} - {subsystem_name}",
                )

    logging.info("=" * 80)
    logging.info("--- ERD Generation Pipeline Finished ---")


if __name__ == "__main__":
    main()
