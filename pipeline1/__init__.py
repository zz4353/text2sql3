
from llm_client import OpenAIClient
from db_client import get_llm_table_schema_context
from .select_columns import select_columns
from .extract_values import extract_values
from .build_sqls import build_sqls

__all__ = ["run", "select_columns", "extract_values", "build_sqls"]

llm = OpenAIClient()

def run(db_id, user_request):
    schema_context = get_llm_table_schema_context(db_id)
    columns = select_columns(db_id, llm, user_request, schema_context)
    selected_column_names = {
        f"{table}.{column}"
        for table, column_list in columns.items()
        for column in column_list
    }
    selected_schema_context = [
        sc for sc in schema_context
        if sc["original_column_name"] in selected_column_names
    ]
    values = extract_values(llm, user_request, columns, selected_schema_context)
    sqls = build_sqls(db_id, values)
    return sqls