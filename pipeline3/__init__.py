
from llm_client import OpenAIClient
from db_client import get_llm_table_schema_context
from .select_columns import select_columns
from .generate_sqls import generate_sqls

llm = OpenAIClient()

def run(db_id, user_request):
    schema_context = get_llm_table_schema_context(db_id)
    columns = select_columns(db_id, llm, user_request, schema_context)
    sqls = generate_sqls(db_id, llm, user_request, columns, schema_context)
    return sqls