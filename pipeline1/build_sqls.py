from db_client import DB_ID, get_required_insert_columns, get_forbidden_insert_columns
from db_client import get_all_unique_indexes, get_table_info, get_column_type
from utils import normalize_value_by_column


def build_sqls(db_id: DB_ID, data: list[dict]) -> list[tuple]:
    """
    data: [{"table": str, "operation": str|None, "records": list[dict]}]
    returns: list of (sql, params, missing_required_columns) per group
    """
    results = []
    for group in data:
        table = group["table"]
        operation = group.get("operation")
        records = group.get("records", [])
        if not records:
            continue
        sqls = _build_for_table(db_id, table, operation, records)
        results.extend(sqls)
    return results


def _build_for_table(db_id: DB_ID, table: str, operation, records: list[dict]) -> list[tuple]:
    required = get_required_insert_columns(db_id, table)
    forbidden = set(get_forbidden_insert_columns(db_id, table))
    results = []

    for record in records:
        columns = [col for col in record.keys() if col not in forbidden]
        missing_required = [col for col in required if col not in columns]
        if missing_required:
            results.append(("", [], missing_required))
            continue

        sql, params = _build_insert_sql(db_id, table, columns, record)
        on_conflict = _build_on_conflict(db_id, table, columns, operation)
        sql = sql[:-1] + f"\n{on_conflict}"
        results.append((sql, params, []))

    return results


def _build_insert_sql(db_id: DB_ID, table: str, columns: list[str], record: dict) -> tuple:
    placeholders = "(" + ", ".join(["?"] * len(columns)) + ")"
    params = []
    for col in columns:
        val = record.get(col)
        col_type = get_column_type(db_id, table, col)
        params.append(normalize_value_by_column(val, col_type))

    sql = f'INSERT INTO "{table}" ("' + '", "'.join(columns) + f'")\nVALUES {placeholders};'
    return sql, params


def _build_on_conflict(db_id: DB_ID, table: str, columns: list[str], operation) -> str:
    if operation is None:
        return "ON CONFLICT DO NOTHING;"

    table_info = get_table_info(db_id, table)
    unique_indexes = get_all_unique_indexes(db_id, table)
    unique_indexes = [
        idx for idx in unique_indexes
        if all(
            col in columns or
            (table_info[col]["notnull"] == 0 and table_info[col]["dflt_value"] in [None, "NULL"])
            for col in idx
        )
    ]

    if len(unique_indexes) == 1:
        conflict_cols = unique_indexes[0]
        update_cols = [col for col in columns if col not in conflict_cols]
        conflict_target = ", ".join([f'"{c}"' for c in conflict_cols])
        if update_cols:
            set_clause = ", ".join([f'"{col}" = excluded."{col}"' for col in update_cols])
            return f"ON CONFLICT ({conflict_target}) DO UPDATE SET {set_clause};"
        return f"ON CONFLICT ({conflict_target}) DO NOTHING;"

    return "ON CONFLICT DO NOTHING;"
