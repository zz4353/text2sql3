import json
from llm_client import OpenAIClient
from pipeline2.select_columns import select_columns
from db_client import get_llm_table_schema_context, DB_ID

with open("test.json", encoding="utf-8") as f:
    test = json.load(f)

sample = test[0]

llm = OpenAIClient()
user_request = sample['user_request']
schema_context = get_llm_table_schema_context(DB_ID(sample['db_id']))
# schema_context = [sc for sc in schema_context if sc["original_column_name"] in columns]

print(select_columns(DB_ID(sample['db_id']), llm, user_request, schema_context))