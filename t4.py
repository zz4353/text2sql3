import json
from llm_client import OpenAIClient
from pipeline1.select_columns import select_columns
from db_client import get_llm_table_schema_context, DB_ID

with open("test.json", encoding="utf-8") as f:
    test = json.load(f)

llm = OpenAIClient()
results = []

for sample in test:
    item_id = sample["id"]
    try:
        schema_context = get_llm_table_schema_context(DB_ID(sample["db_id"]))
        selected = select_columns(DB_ID(sample["db_id"]), llm, sample["user_request"], schema_context)
        results.append({"id": item_id, "db_id": sample["db_id"], "selected_columns": selected})
        print(f"[{item_id}/360] OK")
    except Exception as e:
        results.append({"id": item_id, "db_id": sample["db_id"], "error": str(e)})
        print(f"[{item_id}/360] ERROR: {e}")

output_path = "results_pipeline1_select_columns_by_id.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"\nSaved {len(results)} results to {output_path}")
