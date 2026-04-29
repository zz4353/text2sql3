""" 
Dữ liệu đầu vào để tạo sql ở dạng sau:
[
  {
    "frpm.CDSCode": "234235234235",
    "frpm.School Name": "Greenwood Academy",
    "frpm.District Name": "Greenwood Unified",
    "frpm.County Name": "Santa Clara",
    "frpm.Academic Year": "2021-2022"
  },
  {
    "frpm.CDSCode": "345345345345", 
    "frpm.School Name": "Riverside High School",
    "frpm.District Name": "Riverside Unified",
    "frpm.County Name": "Riverside",
    "frpm.Academic Year": "2020-2021"
  },
  {
    "frpm.CDSCode": "456456456456",
    "frpm.School Name": "Maple Leaf Academy",
    "frpm.District Name": "Maple Valley School District",
    "frpm.County Name": "San Mateo",
    "frpm.Academic Year": "2022-2023"
  },
]
"""

import os
from llm_client import OpenAIClient
from db_client import get_forbidden_insert_columns, get_llm_table_schema_context, get_required_insert_columns, get_column_type, get_all_table_column_names
from db_client import get_all_unique_indexes, get_table_info
from utils import normalize_value_by_column, fuzzy_match, render_prompt

llm = OpenAIClient()


# def _normalize_records_with_fuzzy_columns(records: list[dict], all_columns: list[str], cutoff: float = 0.7, ):
#     normalized_records = []
#     ignored_data = []

#     for record in records:
#         normalized_record = {}
#         for raw_key, value in record.items():
#             matched_key = fuzzy_match(raw_key, all_columns, cutoff=cutoff)
#             if matched_key:
#                 normalized_record[matched_key] = value 
#             else:
#                 ignored_data.append(raw_key)
#         normalized_records.append(normalized_record)

#     return normalized_records, ignored_data


def generate_sql(db_id, data, operation=None):
    # Xử lý map tên bảng, cột về tên bảng, cột thật theo database.  fuzzy matching...
    # all_columns = get_all_table_column_names(db_id)
    # data, ignored_data = _normalize_records_with_fuzzy_columns(data, all_columns)

    # Lấy tên bảng và cột lưu vào dict 'table' có dạng {table_name: [column_name1, column_name2,...]}
    table = {}
    for col in data[0].keys():
        table_name, column_name = col.split('.')
        if table_name not in table:
            table[table_name] = []
        table[table_name].append(column_name)

    return _generate_sql(db_id, table, data, operation)

def z(unique_index, columns, table_info):
    for col in unique_index:
        if col not in columns:
            if table_info[col]['notnull'] == 0 and table_info[col]["dflt_value"] in [None, "NULL"]:
                return False
    return True

def _generate_on_conflict_clause(column_descriptions, columns, unique_indexes, user_requirement=""):
    template_path = os.path.join(os.path.dirname(__file__), "templates/on_conflict_clause_prompt.md")
    prompt = render_prompt(template_path, column_descriptions=column_descriptions, columns=columns, unique_indexes=unique_indexes, user_requirement=user_requirement)
    response = llm.call_llm(prompt).strip()
    return response
 

# def _generate_sql1(db_id, table, data):
#     sqls = []

#     # Tạo SQL cho từng bảng
#     for table_name, columns in table.items():
#         sql, params = "", []
#         required_columns = get_required_insert_columns(db_id, table_name)
#         missing_required_columns = [col for col in required_columns if col not in columns]
#         table_info = get_table_info(db_id, table_name)

#         if len(missing_required_columns) == 0:
#             forbidden_columns = get_forbidden_insert_columns(db_id, table_name)
#             columns = [col for col in columns if col not in forbidden_columns]

#             sql, params = _generate_insert_sql(db_id, table_name, columns, data)

#             unique_indexes = get_all_unique_indexes(db_id, table_name)
#             unique_indexes = [unique_index for unique_index in unique_indexes if z(unique_index, columns, table_info)]

#             if len(unique_indexes) > 0:
#                 # if len(unique_indexes) == 1:
#                     # sql = sql[:-1] + f"\nON CONFLICT ({', '.join(unique_index)}) DO NOTHING;"

#                 schema_context = get_llm_table_schema_context(db_id)  
#                 column_descriptions = []
#                 for sc in schema_context:
#                     if sc["original_column_name"] in columns:
#                         column_descriptions.append(sc)
#                     else:
#                         for unique_index in unique_indexes:
#                             if sc["original_column_name"] in unique_index:
#                                 column_descriptions.append(sc)

#                 response = _generate_on_conflict_clause(column_descriptions, columns, unique_indexes)
#                 if response[-1] != ";":
#                     response += ";"
#                 sql = sql[:-1] + f"\n{response}"

#         sqls.append((sql, params, missing_required_columns))
    
#     return sqls


def _generate_sql(db_id, table, data, operation=None):
    sqls = []

    for table_name, columns in table.items():
        sql, params = "", []
        required_columns = get_required_insert_columns(db_id, table_name)
        missing_required_columns = [col for col in required_columns if col not in columns]
        table_info = get_table_info(db_id, table_name)

        if len(missing_required_columns) == 0:
            forbidden_columns = get_forbidden_insert_columns(db_id, table_name)
            columns = [col for col in columns if col not in forbidden_columns]

            sql, params = _generate_insert_sql(db_id, table_name, columns, data)

            if operation is None:
                sql = sql[:-1] + "\nON CONFLICT DO NOTHING;"
            else:
                unique_indexes = get_all_unique_indexes(db_id, table_name)
                unique_indexes = [unique_index for unique_index in unique_indexes if z(unique_index, columns, table_info)]

                if len(unique_indexes) == 1:
                    conflict_cols = unique_indexes[0]
                    update_cols = [col for col in columns if col not in conflict_cols]
                    conflict_target = ", ".join([f'"{c}"' for c in conflict_cols])
                    if update_cols:
                        set_clause = ", ".join([f'"{col}" = excluded."{col}"' for col in update_cols])
                        on_conflict = f"ON CONFLICT ({conflict_target}) DO UPDATE SET {set_clause};"
                    else:
                        on_conflict = f"ON CONFLICT ({conflict_target}) DO NOTHING;"
                    sql = sql[:-1] + f"\n{on_conflict}"
                elif len(unique_indexes) > 1:
                    sql = sql[:-1] + "\nON CONFLICT DO NOTHING;"

        sqls.append((sql, params, missing_required_columns))

    return sqls


def _generate_insert_sql(db_id, table_name, columns, data):
    placeholders = "(" + ", ".join(["?"] * len(columns)) + ")"
    all_placeholders = []
    params = []

    for row in data:
        all_placeholders.append(placeholders)
        for col in columns:
            val = row[f"{table_name}.{col}"]
            col_type = get_column_type(db_id, table_name, col)
            val = normalize_value_by_column(val, col_type)
            params.append(val)

    values_sql = ",\n       ".join(all_placeholders)
    sql = f'''INSERT INTO {table_name} ("{'", "'.join(columns)}")\nVALUES {values_sql};'''
    return sql, params
