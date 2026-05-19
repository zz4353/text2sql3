import json, re

with open("test.json", "r", encoding="utf-8") as f:
    item = json.load(f)[0]

match = re.search(r"```json\s*\n(.*?)\n```", item["user_request"], re.DOTALL)
gold = json.loads(match.group(1))

from db_client import DB_ID, get_llm_table_schema_context
from pipeline4.extract_values import extract_values
from llm_client import OpenAIClient

selected_columns = {"expense": ["expense_id", "expense_date", "approved"]}
db_id = DB_ID(item["db_id"])
full_schema = get_llm_table_schema_context(db_id)
selected_set = {f"{t}.{c}" for t, cols in selected_columns.items() for c in cols}
schema_context = [sc for sc in full_schema if sc["original_column_name"] in selected_set]

llm = OpenAIClient()
result = extract_values(llm, item["user_request"], selected_columns, schema_context)
pred = result[0]["records"] if result else []

print(f"Gold: {len(gold)} records")
gold_true = sum(1 for r in gold if r["approved"] == "true")
gold_false = sum(1 for r in gold if r["approved"] == "false")
print(f"Gold approved: true={gold_true}, false={gold_false}")

print(f"\nPred: {len(pred)} records")
pred_true = sum(1 for r in pred if r.get("approved") == "true")
pred_false = sum(1 for r in pred if r.get("approved") == "false")
print(f"Pred approved: true={pred_true}, false={pred_false}")
print(f"Pred operation: {result[0].get('operation') if result else 'N/A'}")

# Check expense_id exact match
gold_ids = set(r["expense id"] for r in gold)
pred_ids = set(r.get("expense_id", "") for r in pred)
exact_id_match = gold_ids & pred_ids
print(f"\nExpense ID exact match: {len(exact_id_match)}/{len(gold_ids)}")
