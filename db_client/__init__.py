import os
import sqlite3
import json
from enum import Enum
from utils import remove_alignment_schema, read_csv_with_fallback, fuzzy_match


class DB_ID(str, Enum):
    CALIFORNIA_SCHOOLS = "california_schools"
    CARD_GAMES = "card_games"
    CODEBASE_COMMUNITY = "codebase_community"
    DEBIT_CARD_SPECIALIZING = "debit_card_specializing"
    EUROPEAN_FOOTBALL_2 = "european_football_2"
    FINANCIAL = "financial"
    FORMULA_1 = "formula_1"
    STUDENT_CLUB = "student_club"
    SUPERHERO = "superhero"
    THROMBOSIS_PREDICTION = "thrombosis_prediction"
    TOXICOLOGY = "toxicology"

_BASE_DIR = "datasets/bird/dev_databases"
DB_PATH = {
    DB_ID.CALIFORNIA_SCHOOLS: os.path.join(_BASE_DIR, "california_schools/california_schools.sqlite"),
    DB_ID.CARD_GAMES: os.path.join(_BASE_DIR, "card_games/card_games.sqlite"),
    DB_ID.CODEBASE_COMMUNITY: os.path.join(_BASE_DIR, "codebase_community/codebase_community.sqlite"),
    DB_ID.DEBIT_CARD_SPECIALIZING: os.path.join(_BASE_DIR, "debit_card_specializing/debit_card_specializing.sqlite"),
    DB_ID.EUROPEAN_FOOTBALL_2: os.path.join(_BASE_DIR, "european_football_2/european_football_2.sqlite"),
    DB_ID.FINANCIAL: os.path.join(_BASE_DIR, "financial/financial.sqlite"),
    DB_ID.FORMULA_1: os.path.join(_BASE_DIR, "formula_1/formula_1.sqlite"),
    DB_ID.STUDENT_CLUB: os.path.join(_BASE_DIR, "student_club/student_club.sqlite"),
    DB_ID.SUPERHERO: os.path.join(_BASE_DIR, "superhero/superhero.sqlite"),
    DB_ID.THROMBOSIS_PREDICTION: os.path.join(_BASE_DIR, "thrombosis_prediction/thrombosis_prediction.sqlite"),
    DB_ID.TOXICOLOGY: os.path.join(_BASE_DIR, "toxicology/toxicology.sqlite"),
}

def get_all_unique_indexes(db_id: DB_ID, table_name: str):
    db_path = DB_PATH[db_id]
    unique_indexes = []

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA index_list('{table_name}')")
        indexes = cursor.fetchall()

        for idx in indexes:
            idx_name = idx[1]
            is_unique = idx[2]
            origin = idx[3]

            if is_unique == 1:
                cursor.execute(f"PRAGMA index_info('{idx_name}')")
                columns = cursor.fetchall()
                column_names = [col[2] for col in columns]
                unique_indexes.append(column_names)

    return unique_indexes

def get_database_schema(db_id: DB_ID) -> dict[str, str]:
    db_path = DB_PATH[db_id]

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            select sql
            from sqlite_master 
            where sql is not null;
        """)

        return [remove_alignment_schema(sql[0]) for sql in cursor.fetchall()]
    
def get_table_samples(db_id: DB_ID, table_name: str, first_n: int = 5, random_n: int = 5):
    db_path = DB_PATH[db_id]

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            f"""
            SELECT *
            FROM "{table_name}"
            ORDER BY rowid
            LIMIT ?;
            """,
            (first_n,)
        )
        first_rows = cursor.fetchall()

        cursor.execute(
            f"SELECT * FROM '{table_name}' ORDER BY RANDOM() LIMIT ?;",
            (random_n,)
        )
        random_rows = cursor.fetchall() 
        
        rows = first_rows + random_rows

        if not rows:
            return {}

        samples = {k: [] for k in rows[0].keys()}

        for row in rows:
            for col in row.keys():
                samples[col].append(row[col])

        return samples


def get_all_table_names(db_id: DB_ID) -> list[str]:
    db_path = DB_PATH[db_id]

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%';
        """)
        return [row[0] for row in cursor.fetchall()]

def get_table_descriptions_from_csv(db_id: DB_ID, table_name: str): 
    path = os.path.join(_BASE_DIR, db_id.value,"database_description", f"{table_name}.csv")
    
    if not os.path.exists(path):
        raise FileNotFoundError(f"Description file not found: {path}")
    
    descriptions = []

    reader = read_csv_with_fallback(path)
    for row in reader:
        descriptions.append(row)

    return descriptions

def get_all_table_descriptions_from_csv(db_id: DB_ID):
    base_path = os.path.join(_BASE_DIR, db_id.value, "database_description")
    
    if not os.path.exists(base_path):
        raise FileNotFoundError(f"Description directory not found: {base_path}")
    
    all_tables = get_all_table_names(db_id)
    all_descriptions = {}
    for table in all_tables:
        descriptions = get_table_descriptions_from_csv(db_id, table)
        all_descriptions[table] = descriptions

    return all_descriptions

def create_llm_table_schema_context_jsonl(db_id: DB_ID, output_path: str):
    all_tables = get_all_table_names(db_id)
    all_columns = get_all_table_column_names(db_id) 

    schema_contexts = []
    for table in all_tables:
        descriptions_csv = get_table_descriptions_from_csv(db_id, table)
        table_info = get_table_info(db_id, table)
        samples = get_table_samples(db_id, table)
        
        for desc in descriptions_csv:
            _desc = {
                "original_column_name": fuzzy_match(f"{table}.{desc['original_column_name']}", all_columns), 
                "column_name": desc.get("column_name", ""),
                "column_description": desc.get("column_description", ""),
                "data_format": desc.get("data_format", ""),
                "value_description": desc.get("value_description", ""),
            }
            column_name = _desc["original_column_name"].split(".", 1)[1]
            _desc["samples"] = samples.get(column_name, [])
            _desc["notnull"] = table_info[column_name]["notnull"]
            schema_contexts.append(_desc)           

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for schema_context in schema_contexts:
            f.write(json.dumps(schema_context, ensure_ascii=False) + "\n")    

def get_llm_table_schema_context(db_id: DB_ID):
    path= f"datasets/bird/llm_schema_contexts/{db_id.value}.jsonl"
    schema_context = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            schema_context.append(json.loads(line))
    return schema_context


def get_column_type(db_id: DB_ID, table_name: str, column_name: str) -> str:
    db_path = DB_PATH[db_id]
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        cursor.execute(f'PRAGMA table_info("{table_name}")')
        rows = cursor.fetchall()

        for row in rows:
            # PRAGMA table_info columns:
            # (cid, name, type, notnull, dflt_value, pk)
            _, name, col_type, _, _, _ = row
            if name == column_name:
                return col_type

        raise ValueError(f"Column '{column_name}' not found in table '{table_name}'")
    
def get_required_insert_columns(db_id: DB_ID, table_name: str) -> list[str]:
    """ Hàm này trả về các cột bắt buộc phải xuất hiện trong insert
    - Các cột not null nhưng loại bỏ các trường hợp sau:
        - Loại bỏ primary key khỏi danh sách các cột not null nếu kiểu dữ liệu của nó là INTEGER 
        - Loại bỏ các cột có giá trị mặc định (default value), nếu cột unique vẫn loại bỏ.
    - Trường hợp NOT NULL + default value NULL -> vẫn yêu cầu trong câu insert phải có cột này.
    """
    db_path = DB_PATH[db_id]

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info('{table_name}')")
        rows = cursor.fetchall()

        # (cid, name, type, notnull, dflt_value, pk)
        result = []
        pk = len([row for row in rows if row[5] > 0])  # primary key

        for row in rows:
            # Lấy các cột not null
            if row[3] == 1:  # notnull
                # Nếu có giá trị mặc định khác NULL thì bỏ qua. None là không có giá trị mặc định. "NULL" là giá trị mặc định là NULL.
                if row[4] not in (None, "NULL") :  # default value
                    continue

                # trường hợp chỉ có 1 primary key và kiểu dữ liệu là INTEGER thì cột này sẽ tự động tăng
                if pk == 1 and row[5] > 0:  # primary key  
                    if row[2].upper() == "INTEGER":  # type
                        continue
                result.append(row[1])
        return result
    
def get_forbidden_insert_columns(db_id: DB_ID, table_name: str) -> list[str]:
    """ Hàm này trả về các cột không được phép xuất hiện trong insert 
        - Bao gồm các cột ẩn, cột generated,...
    """
    db_path = DB_PATH[db_id]

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_xinfo('{table_name}')")
        rows = cursor.fetchall()
        xrows = [row[1] for row in rows if row[6] > 0]  # hidden columns
        return xrows
    
def get_table_info(db_id: DB_ID, table_name: str):
    """cid, name, type, notnull, dflt_value, pk"""
    db_path = DB_PATH[db_id]

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info('{table_name}')")
        rows = cursor.fetchall()

        d = {}
        for row in rows:
            column_name = row[1]
            d[column_name] = {
                "cid": row[0],
                "type": row[2],
                "notnull": row[3],
                "dflt_value": row[4],
                "pk": row[5],
            }

        return d

def get_table_xinfo(db_id: DB_ID, table_name: str):
    """cid, name, type, notnull, dflt_value, pk, hidden"""
    db_path = DB_PATH[db_id]

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_xinfo('{table_name}')")
        rows = cursor.fetchall()

        d = {}
        for row in rows:
            column_name = row[1]
            d[column_name] = {
                "cid": row[0],
                "type": row[2],
                "notnull": row[3],
                "dflt_value": row[4],
                "pk": row[5],
                "hidden": row[6],
            }

        return d
    
def get_all_table_column_names(db_id: DB_ID):
    tables = get_all_table_names(db_id)

    result = []
    for table in tables:
        columns = get_table_info(db_id, table).keys()
        columns = [f"{table}.{col}" for col in columns]
        result.extend(columns)

    return tuple(result)

def get_all_table_column_names2(db_id: DB_ID) -> dict[str, list[str]]:
    return {table: list(get_table_info(db_id, table).keys()) for table in get_all_table_names(db_id)}

def get_foreign_key_references(db_id: DB_ID, columns: list[str]) -> list[str]:
    """Trả về danh sách các cột mà các cột trong `columns` tham chiếu khóa ngoại đến.

    Args:
        db_id: ID của database
        columns: danh sách cột dạng ["table.column", ...]

    Returns:
        Danh sách các cột được tham chiếu, dạng ["table.column", ...], không trùng lặp.
    """
    db_path = DB_PATH[db_id]

    # Parse input thành dict: {table: [col1, col2, ...]}
    table_cols: dict[str, list[str]] = {}
    for item in columns:
        table, col = item.split(".", 1)
        table_cols.setdefault(table, []).append(col)

    referenced = []
    seen = set()

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        for table, cols in table_cols.items():
            cursor.execute(f"PRAGMA foreign_key_list('{table}')")
            fk_rows = cursor.fetchall()
            # PRAGMA foreign_key_list columns:
            # (id, seq, table, from, to, on_update, on_delete, match)
            for row in fk_rows:
                from_col = row[3]
                to_table = row[2]
                to_col = row[4]
                if from_col in cols:
                    # to_col is NULL when FK references PK implicitly (no target column specified)
                    if to_col is None:
                        cursor.execute(f"PRAGMA table_info('{to_table}')")
                        pk_cols = [r[1] for r in cursor.fetchall() if r[5] > 0]
                        to_col = pk_cols[0] if pk_cols else None
                    if to_col is None:
                        continue
                    ref = f"{to_table}.{to_col}"
                    if ref not in seen:
                        seen.add(ref)
                        referenced.append(ref)

    return referenced


def get_all_foreign_keys(db_id: DB_ID) -> list[dict]:
    """Trả về danh sách tất cả khóa ngoại trong database.

    Returns:
        List các dict với các key:
            - from_table: bảng chứa khóa ngoại
            - from_col: cột khóa ngoại
            - to_table: bảng được tham chiếu
            - to_col: cột được tham chiếu
    """
    db_path = DB_PATH[db_id]
    result = []

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
        """)
        tables = [row[0] for row in cursor.fetchall()]

        for table in tables:
            cursor.execute(f"PRAGMA foreign_key_list('{table}')")
            fk_rows = cursor.fetchall()
            # (id, seq, table, from, to, on_update, on_delete, match)
            for row in fk_rows:
                from_col = row[3]
                to_table = row[2]
                to_col = row[4]
                if to_col is None:
                    cursor.execute(f"PRAGMA table_info('{to_table}')")
                    pk_cols = [r[1] for r in cursor.fetchall() if r[5] > 0]
                    to_col = pk_cols[0] if pk_cols else None
                if to_col is None:
                    continue
                result.append({
                    "from_table": table,
                    "from_col": from_col,
                    "to_table": to_table,
                    "to_col": to_col,
                })

    return result


def clone_db_to_memory(db_id: DB_ID):
    disk_conn = sqlite3.connect(DB_PATH[db_id])
    mem_conn = sqlite3.connect(":memory:")

    disk_conn.backup(mem_conn)
    disk_conn.close()

    mem_conn.execute("PRAGMA foreign_keys = ON")
    return mem_conn