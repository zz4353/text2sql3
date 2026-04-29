import os
import json
from db_client import DB_ID, get_all_foreign_keys, get_all_table_column_names2
from db_client import get_required_insert_columns, get_forbidden_insert_columns
from utils import render_prompt, extract_columns_from_insert, fuzzy_match


def select_columns(db_id: DB_ID, llm, user_input, schema_context):
    template_path = os.path.join(os.path.dirname(__file__), "templates/select_cols.md")
    foreign_keys = get_all_foreign_keys(db_id)
    prompt = render_prompt(template_path, user_input=user_input, schema=schema_context, foreign_keys=foreign_keys)

    llm_raw_result = llm.call_llm(prompt, text={"format": {"type": "json_object"}})
    llm_raw_result = extract_columns_from_insert(json.loads(llm_raw_result)['sql'])

    # Kiểm tra và map các cột trả về với cột thực tế trong database.
    all_columns = get_all_table_column_names2(db_id)
    valid_cols = _map_to_valid_columns(llm_raw_result, all_columns)

    # Thêm các cột bắt buộc, xóa các cột tự sinh,...
    result = _apply_column_constraints(db_id, valid_cols)
    return result


def _map_to_valid_columns(raw_cols: dict[str, list[str]], all_columns: dict[str, list[str]]) -> dict[str, list[str]]:
    result = {}
    for table, cols in raw_cols.items():
        if table not in all_columns:
            table = fuzzy_match(table, tuple(all_columns), cutoff=0.8)
            if not table:
                continue
        candidates = tuple(all_columns[table])
        matched_cols = []
        for col in cols:
            matched = fuzzy_match(col, candidates)
            if matched and matched not in matched_cols:
                matched_cols.append(matched)
        if matched_cols:
            result[table] = matched_cols
    return result


def _apply_column_constraints(db_id: DB_ID, valid_cols: dict[str, list[str]]) -> dict[str, list[str]]:
    result = {}
    for table, cols in valid_cols.items():
        required = get_required_insert_columns(db_id, table)
        forbidden = set(get_forbidden_insert_columns(db_id, table))
        filtered = [col for col in cols if col not in forbidden]
        for col in required:
            if col not in filtered:
                filtered.append(col)
        if filtered:
            result[table] = filtered
    return result