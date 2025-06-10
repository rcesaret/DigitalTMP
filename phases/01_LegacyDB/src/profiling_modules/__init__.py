# -*- coding: utf-8 -*-
"""
Profiling Modules Package for Digital TMP.

This package contains a collection of modules designed to perform a deep and
quantitative analysis of PostgreSQL databases. Each module is responsible for a
specific category of metrics, from basic database statistics to complex,
heuristic measures of interoperability.

The modules are designed to be called by an orchestrator script, which will
pass a SQLAlchemy engine object and relevant parameters (like schema names)
to the functions within.

Package Structure:
    - base.py: Core utility functions for discovering database objects.
    - metrics_basic.py: Database and schema-level summary statistics.
    - metrics_schema.py: Structural metrics for tables and columns.
    - metrics_profile.py: Data content profiling (NULLs, cardinality).
    - metrics_interop.py: Custom heuristic metrics (JDI, LIF, NF).
    - metrics_performance.py: Canonical query performance benchmarking.

"""