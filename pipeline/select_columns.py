import os
import json
from db_client import DB_ID, get_all_foreign_keys, get_all_table_column_names
from db_client import get_required_insert_columns, get_forbidden_insert_columns
from utils import render_prompt, extract_columns_from_insert, fuzzy_match


def select_columns(db_id: DB_ID, llm, user_input, schema_context):
    template_path = os.path.join(os.path.dirname(__file__), "templates/select_cols.md")
    foreign_keys = get_all_foreign_keys(db_id)
    prompt = render_prompt(template_path, user_input=user_input, schema=schema_context, foreign_keys=foreign_keys)

    llm_raw_result = llm.call_llm(prompt, text={"format": {"type": "json_object"}})
    llm_raw_result = extract_columns_from_insert(json.loads(llm_raw_result)['sql'])

    # Kiểm tra và map các cột trả về với cột thực tế trong database.
    all_columns = get_all_table_column_names(db_id)
    valid_cols = _map_to_valid_columns(llm_raw_result, all_columns)

    # Thêm các cột bắt buộc, xóa các cột tự sinh,...
    result = _apply_column_constraints(db_id, valid_cols)
    return result


def _map_to_valid_columns(raw_cols: list[str], all_columns: list[str]) -> list[str]:
    valid_cols = []
    for col in raw_cols:
        matched = fuzzy_match(col, all_columns)
        if matched and matched not in valid_cols:
            valid_cols.append(matched)
    return valid_cols


def _apply_column_constraints(db_id: DB_ID, valid_cols: list[str]) -> list[str]:
    tables = []
    for col in valid_cols:
        table = col.split('.', 1)[0]
        if table not in tables:
            tables.append(table)

    result = []
    for table in tables:
        table_cols = [col for col in valid_cols if col.startswith(f"{table}.")]
        required = [f"{table}.{col}" for col in get_required_insert_columns(db_id, table)]
        forbidden = [f"{table}.{col}" for col in get_forbidden_insert_columns(db_id, table)]
        table_cols = [col for col in table_cols if col not in forbidden]
        for col in required:
            if col not in table_cols:
                table_cols.append(col)
        result.extend(table_cols)
    return tuple(result)