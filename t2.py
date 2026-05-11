import json
from db_client import DB_ID, get_llm_table_schema_context
from pipeline4.extract_values import extract_values
from llm_client import OpenAIClient

with open("test.json", "r", encoding="utf-8") as f:
    test_data = json.load(f)

item = test_data[0]
db_id = DB_ID(item["db_id"])
user_request = item["user_request"]

# Giả lập kết quả select_columns
selected_columns = {
    "expense": ["expense_id", "expense_date", "approved"]
}

# Lọc schema theo selected_columns
full_schema = get_llm_table_schema_context(db_id)
selected_set = {
    f"{table}.{col}"
    for table, cols in selected_columns.items()
    for col in cols
}
schema_context = [sc for sc in full_schema if sc["original_column_name"] in selected_set]

print(f"db_id: {db_id}")
print(f"user_request: {user_request[:100]}...")
print(f"selected_columns: {selected_columns}")
print(f"schema_context entries: {len(schema_context)}")

llm = OpenAIClient()
result = extract_values(llm, user_request, selected_columns, schema_context)
print(f"\nResult ({len(result)} groups):")
print(json.dumps(result, indent=2, ensure_ascii=False))
