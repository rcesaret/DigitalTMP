
# schema_viz.py
"""
Generate Entity-Relationship Diagrams (ERDs) for a PostgreSQL database using
SQLAlchemy metadata reflection and Graphviz via sqlalchemy_schemadisplay.

Usage:
	python schema_viz.py \
	  --db-url postgresql://user:pass@localhost:5432/mydb \
	  --output-dir docs/er
"""
import argparse
import os
from sqlalchemy import create_engine, MetaData
from sqlalchemy_schemadisplay import create_schema_graph


def parse_args():
	parser = argparse.ArgumentParser(
		description="Generate ERD SVGs for a PostgreSQL database."
	)
	parser.add_argument(
		'--db-url', required=True,
		help='SQLAlchemy database URL for target PostgreSQL database'
	)
	parser.add_argument(
		'--output-dir', default='docs/er',
		help='Directory to write ERD SVGs'
	)
	return parser.parse_args()


def ensure_output_dir(path):
	"""Create output directory if it doesn't exist."""
	os.makedirs(path, exist_ok=True)


def generate_erd(db_url, output_dir):
	"""
	Reflect the public schema and create an ERD SVG.
	"""
	engine = create_engine(db_url)
	metadata = MetaData()
	# Reflect only public schema tables
	metadata.reflect(bind=engine, schema='public')

	# Create the graph object
	graph = create_schema_graph(
		metadata=metadata,
		show_datatypes=False,	   # hide datatypes in boxes
		show_indexes=False,		 # hide index info
		rankdir='LR',			   # left-to-right layout
		concentrate=False,
		font='Helvetica'
	)

	# Determine output filename based on database name
	db_name = engine.url.database
	out_path = os.path.join(output_dir, f"{db_name}_erd.svg")

	# Write SVG to file
	graph.write_svg(out_path)
	print(f"ERD generated: {out_path}")


def main():
	args = parse_args()
	ensure_output_dir(args.output_dir)
	generate_erd(args.db_url, args.output_dir)


if __name__ == '__main__':
	main()
