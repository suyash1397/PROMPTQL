"""
   introspect.py

   A production-level utility for relational database schema introspection:
   - Collects tables, columns, primary keys, foreign keys, indexes
   - Discovers relationships and dependencies
   - Exports schema metadata to JSON or DOT (Graphviz) for visualization

   Usage:
       python introspect.py --url postgresql://user:pass@host:port/dbname \
           [--format json|dot] [--output schema.json]
   """
import argparse
import json
import logging
import sys
from collections import defaultdict
from typing import Dict, List, Any

from sqlalchemy import create_engine, MetaData, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

# Configure root logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_engine(db_url: str) -> Engine:
    """Create SQLAlchemy engine for given database URL."""
    try:
        engine = create_engine(db_url)
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return engine
    except Exception as e:
        logger.error(f"Failed to create engine or connect: {e}")
        raise


def introspect_metadata(engine: Engine) -> MetaData:
    """Reflect database schema into SQLAlchemy MetaData."""
    metadata = MetaData()
    metadata.reflect(bind=engine)
    logger.info(f"Reflected tables: {list(metadata.tables)}")
    return metadata


def get_db_objects(inspector, dialect, include_views=False, include_matviews=False, schema=None):
    """Get all tables, and optionally views/materialized views, for the current DB dialect."""
    tables, views, matviews = [], [], []
    try:
        if dialect == 'oracle':
            # Oracle: schema is usually uppercase username
            schema = schema or inspector.engine.url.username.upper()
            tables = inspector.get_table_names(schema=schema)
            if include_views:
                views = inspector.get_view_names(schema=schema)
        elif dialect == 'mssql':
            # MSSQL: schema defaults to 'dbo'
            schema = schema or 'dbo'
            tables = inspector.get_table_names(schema=schema)
            if include_views:
                views = inspector.get_view_names(schema=schema)
        else:
            tables = inspector.get_table_names()
            if include_views:
                views = inspector.get_view_names()
        if include_matviews and dialect == 'postgresql':
            try:
                matviews = inspector.get_view_names(view_type='mview')
            except Exception:
                pass
    except Exception as e:
        raise RuntimeError(f"Failed to get DB objects: {e}")
    return tables, views, matviews


def get_table_info(inspector, table_name: str, dialect: str, is_view=False, schema=None) -> Dict[str, Any]:
    """Gather column, PK, FK, and index info for a single table or view, with DB-specific logic."""
    try:
        if dialect == 'oracle':
            schema = schema or inspector.engine.url.username.upper()
            columns = inspector.get_columns(table_name, schema=schema)
        elif dialect == 'mssql':
            schema = schema or 'dbo'
            columns = inspector.get_columns(table_name, schema=schema)
        else:
            columns = inspector.get_columns(table_name)
    except Exception as e:
        columns = []
    pk, fks, indexes = [], [], []
    if not is_view:
        try:
            if dialect == 'oracle':
                pk = inspector.get_pk_constraint(
                    table_name, schema=schema).get('constrained_columns', [])
            elif dialect == 'mssql':
                pk = inspector.get_pk_constraint(
                    table_name, schema=schema).get('constrained_columns', [])
            else:
                pk = inspector.get_pk_constraint(
                    table_name).get('constrained_columns', [])
        except Exception:
            pass
        try:
            if dialect == 'oracle':
                fks = inspector.get_foreign_keys(table_name, schema=schema)
            elif dialect == 'mssql':
                fks = inspector.get_foreign_keys(table_name, schema=schema)
            else:
                fks = inspector.get_foreign_keys(table_name)
        except Exception:
            pass
        try:
            if dialect == 'oracle':
                indexes = inspector.get_indexes(table_name, schema=schema)
            elif dialect == 'mssql':
                indexes = inspector.get_indexes(table_name, schema=schema)
            else:
                indexes = inspector.get_indexes(table_name)
        except Exception:
            pass
    return {
        'columns': [col['name'] for col in columns],
        'primary_key': pk,
        'foreign_keys': [
            {'column': fk['constrained_columns'], 'referred_table': fk['referred_table'],
                'referred_columns': fk['referred_columns']}
            for fk in fks
        ],
        'indexes': [idx['column_names'] for idx in indexes]
    }


def detect_many_to_many_advanced(tables_info, config=None):
    """Advanced detection of many-to-many association tables, supporting composite PKs, extra columns, and user heuristics."""
    m2m = []
    for tbl, info in tables_info.items():
        pk_set = set(info['primary_key'])
        fk_cols = set(sum([fk['column'] for fk in info['foreign_keys']], []))
        # Heuristic: all PK cols are FKs, exactly two FKs, and (optionally) no extra columns
        if pk_set == fk_cols and len(info['foreign_keys']) == 2:
            tables = [fk['referred_table'] for fk in info['foreign_keys']]
            m2m.append({'association_table': tbl, 'tables': tables})
        elif config and config.get('allow_extra_columns') and len(info['foreign_keys']) == 2 and pk_set.issubset(fk_cols):
            tables = [fk['referred_table'] for fk in info['foreign_keys']]
            m2m.append({'association_table': tbl, 'tables': tables,
                       'note': 'extra columns present'})
    return m2m


def build_relationships_advanced(tables_info, config=None):
    """Advanced relationship detection supporting composite FKs, user config, and views."""
    rels = []
    for tbl, info in tables_info.items():
        for fk in info['foreign_keys']:
            for col, ref_col in zip(fk['column'], fk['referred_columns']):
                rels.append({
                    'from_table': tbl,
                    'from_column': col,
                    'to_table': fk['referred_table'],
                    'to_column': ref_col
                })
    return rels


def build_dependency_graph(relationships: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """Create a dependency graph mapping each table to tables it depends on."""
    graph = defaultdict(list)
    for rel in relationships:
        graph[rel['from_table']].append(rel['to_table'])
    logger.info(f"Dependency graph: {dict(graph)}")
    return graph


def export_schema_json(tables_info: Dict[str, Any], relationships: List[Dict[str, Any]], m2m: List[Dict[str, Any]], graph: Dict[str, List[str]], output: str) -> None:
    """Write full schema metadata to a JSON file."""
    schema = {
        'tables': tables_info,
        'relationships': relationships,
        'many_to_many': m2m,
        'dependency_graph': graph
    }
    with open(output, 'w', encoding='utf-8') as f:
        json.dump(schema, f, indent=2)
    logger.info(f"Schema exported to {output}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Database schema introspection tool")
    parser.add_argument('--url', required=True,
                        help='Database URL (SQLAlchemy format)')
    parser.add_argument(
        '--format', choices=['json', 'dot'], default='json', help='Export format')
    parser.add_argument('--output', default='schema.json',
                        help='Output file path')
    parser.add_argument('--include-views', action='store_true',
                        help='Include views in introspection')
    parser.add_argument('--include-matviews', action='store_true',
                        help='Include materialized views (Postgres only)')
    parser.add_argument('--m2m-extra-columns', action='store_true',
                        help='Allow extra columns in many-to-many association tables')
    parser.add_argument('--schema', default=None,
                        help='Explicit DB schema (for Oracle/MSSQL)')
    parser.add_argument('--error-json', action='store_true',
                        help='Output errors as structured JSON')
    return parser.parse_args()


def main():
    args = parse_args()

    def error_exit(msg, code=1, exc=None):
        if args.error_json:
            err = {'error': str(msg), 'code': code}
            if exc:
                err['exception'] = str(exc)
            print(json.dumps(err), file=sys.stderr)
        else:
            logger.error(msg)
            if exc:
                logger.error(str(exc))
        sys.exit(code)
    try:
        engine = get_engine(args.url)
        inspector = inspect(engine)
        dialect = engine.dialect.name
        tables, views, matviews = get_db_objects(
            inspector, dialect, args.include_views, args.include_matviews, args.schema)
        tables_info = {}
        # Introspect tables
        for table_name in tables:
            tables_info[table_name] = get_table_info(
                inspector, table_name, dialect, schema=args.schema)
        # Introspect views
        for view_name in views:
            tables_info[view_name] = get_table_info(
                inspector, view_name, dialect, is_view=True, schema=args.schema)
        # Introspect materialized views (Postgres only)
        for matview_name in matviews:
            tables_info[matview_name] = get_table_info(
                inspector, matview_name, dialect, is_view=True, schema=args.schema)
        # Build relationships
        rel_config = {'allow_extra_columns': args.m2m_extra_columns}
        relationships = build_relationships_advanced(tables_info, rel_config)
        m2m = detect_many_to_many_advanced(tables_info, rel_config)
        graph = build_dependency_graph(relationships)
        # Export
        if args.format == 'json':
            export_schema_json(tables_info, relationships,
                               m2m, graph, args.output)
        else:
            from sqlalchemy_schemadisplay import create_schema_graph
            metadata = MetaData()
            metadata.reflect(bind=engine)
            graphviz = create_schema_graph(
                metadata=metadata, show_datatypes=False, show_indexes=False,
                rankdir='LR')
            graphviz.write(args.output)
            logger.info(f"Graphviz schema diagram exported to {args.output}")
        sys.exit(0)
    except SQLAlchemyError as e:
        error_exit(f"SQLAlchemy error: {e}", code=2, exc=e)
    except Exception as e:
        error_exit(f"Unexpected error: {e}", code=1, exc=e)


def introspect_schema(
    db_url: str,
    include_views: bool = False,
    include_matviews: bool = False,
    m2m_extra_columns: bool = False,
    schema: str = None
) -> dict:
    engine = get_engine(db_url)
    inspector = inspect(engine)
    dialect = engine.dialect.name
    tables, views, matviews = get_db_objects(
        inspector, dialect, include_views, include_matviews, schema)
    tables_info = {}
    for table_name in tables:
        tables_info[table_name] = get_table_info(
            inspector, table_name, dialect, schema=schema)
    for view_name in views:
        tables_info[view_name] = get_table_info(
            inspector, view_name, dialect, is_view=True, schema=schema)
    for matview_name in matviews:
        tables_info[matview_name] = get_table_info(
            inspector, matview_name, dialect, is_view=True, schema=schema)
    rel_config = {'allow_extra_columns': m2m_extra_columns}
    relationships = build_relationships_advanced(tables_info, rel_config)
    m2m = detect_many_to_many_advanced(tables_info, rel_config)
    graph = build_dependency_graph(relationships)
    return {
        'tables': tables_info,
        'relationships': relationships,
        'many_to_many': m2m,
        'dependency_graph': graph
    }


if __name__ == '__main__':
    main()
