import sqlite3
import os
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'restaurant.db')
SCHEMA_PATH = os.path.join(BASE_DIR, 'schema.sql')
SEED_PATH = os.path.join(BASE_DIR, 'seed.sql')

def get_connection():
    """Returns a new sqlite3 database connection with FK enforcement and row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Initializes tables, views, triggers, and indexes from schema.sql."""
    conn = get_connection()
    with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
        schema_sql = f.read()
    conn.executescript(schema_sql)
    conn.commit()
    conn.close()

def seed_database():
    """Fills the database with initial sample restaurant data from seed.sql."""
    conn = get_connection()
    with open(SEED_PATH, 'r', encoding='utf-8') as f:
        seed_sql = f.read()
    conn.executescript(seed_sql)
    conn.commit()
    conn.close()

def query_all(query, params=()):
    """Execute a SELECT query and return list of dict rows."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def query_one(query, params=()):
    """Execute a SELECT query and return a single dict row (or None)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def execute_commit(query, params=()):
    """Execute INSERT/UPDATE/DELETE query and commit. Returns lastrowid or rowcount."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        conn.commit()
        last_id = cursor.lastrowid
        row_count = cursor.rowcount
        return True, {"lastrowid": last_id, "rowcount": row_count}
    except sqlite3.Error as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()

def run_custom_query(sql_statement):
    """
    Executes an arbitrary SQL query from the web playground.
    Returns: {
        'success': bool,
        'columns': list[str],
        'rows': list[list],
        'row_count': int,
        'execution_time_ms': float,
        'query_type': str,
        'message': str
    }
    """
    cleaned_sql = sql_statement.strip()
    if not cleaned_sql:
        return {'success': False, 'message': 'SQL query cannot be empty.'}

    conn = get_connection()
    cursor = conn.cursor()
    start_time = time.perf_counter()
    
    first_word = cleaned_sql.split()[0].upper()

    try:
        if first_word in ('SELECT', 'WITH', 'PRAGMA', 'EXPLAIN'):
            cursor.execute(cleaned_sql)
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            raw_rows = cursor.fetchall()
            rows = [list(row) for row in raw_rows]
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            conn.close()
            return {
                'success': True,
                'query_type': 'SELECT',
                'columns': columns,
                'rows': rows,
                'row_count': len(rows),
                'execution_time_ms': elapsed_ms,
                'message': f"Query executed successfully in {elapsed_ms} ms. Returned {len(rows)} row(s)."
            }
        else:
            # DML / DDL statements
            cursor.execute(cleaned_sql)
            conn.commit()
            affected = cursor.rowcount
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            conn.close()
            return {
                'success': True,
                'query_type': first_word,
                'columns': [],
                'rows': [],
                'row_count': affected,
                'execution_time_ms': elapsed_ms,
                'message': f"Statement executed successfully in {elapsed_ms} ms. {affected} row(s) affected."
            }
    except Exception as e:
        conn.rollback()
        conn.close()
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return {
            'success': False,
            'query_type': first_word,
            'message': f"SQL Error: {str(e)}",
            'execution_time_ms': elapsed_ms
        }

def get_db_metadata():
    """Extracts tables, columns, primary keys, and foreign keys for Schema Viewer."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name;")
    tables = [r[0] for r in cursor.fetchall()]
    
    schema_info = {}
    for table in tables:
        cursor.execute(f"PRAGMA table_info({table});")
        columns = cursor.fetchall()
        
        cursor.execute(f"PRAGMA foreign_key_list({table});")
        fks = cursor.fetchall()
        
        cursor.execute(f"SELECT COUNT(*) FROM {table};")
        count = cursor.fetchone()[0]

        schema_info[table] = {
            'count': count,
            'columns': [
                {
                    'cid': col['cid'],
                    'name': col['name'],
                    'type': col['type'],
                    'notnull': bool(col['notnull']),
                    'dflt_value': col['dflt_value'],
                    'pk': bool(col['pk'])
                }
                for col in columns
            ],
            'foreign_keys': [
                {
                    'id': fk['id'],
                    'seq': fk['seq'],
                    'table': fk['table'],
                    'from': fk['from'],
                    'to': fk['to'],
                    'on_update': fk['on_update'],
                    'on_delete': fk['on_delete']
                }
                for fk in fks
            ]
        }
        
    cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='view' ORDER BY name;")
    views = [{'name': r[0], 'sql': r[1]} for r in cursor.fetchall()]

    cursor.execute("SELECT name, tbl_name, sql FROM sqlite_master WHERE type='trigger' ORDER BY name;")
    triggers = [{'name': r[0], 'table': r[1], 'sql': r[2]} for r in cursor.fetchall()]

    conn.close()
    return {'tables': schema_info, 'views': views, 'triggers': triggers}
