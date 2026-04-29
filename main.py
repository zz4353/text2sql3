from pipeline import run
from db_client import DB_ID
import json

path = "test.json"
with open(path, "r", encoding="utf-8") as file:
    test_set = json.load(file)

count = 0
results = []
for item in test_set:
    try:
        print(item["id"])
        result = run(DB_ID(item["db_id"]), item["user_request"])
        print(result)
        results.append({
            "id": item["id"],
            "db_id": item["db_id"], 
            "pred_sql": result,
            "user_request": item["user_request"],
            })
        if count >= 5:
            # lưu tiếp vào file results.json
            with open("resultsmn.json", "a", encoding="utf-8") as f:
                json.dump(results, f, indent=4)
            results = []
            count = 0
        else:
            count += 1
    except Exception as e:
        print(f"Error processing item with id {item['id']}: {e}")

if results:
    with open("resultsmn.json", "a", encoding="utf-8") as f:
        json.dump(results, f, indent=4)

print("Done!")