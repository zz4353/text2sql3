import json

FILES = {
    "p1_mini":  "results/pipeline1/evaluation.json",
    "p1_gpt41": "results/pipeline1/evaluation_gpt41.json",
    "bl_mini":  "results/baseline/evaluation.json",
    "bl_gpt41": "results/baseline/evaluation_gpt41.json",
}
OUTPUT_PATH = "results/only_p1_mini_wins.json"


def load_match(path) -> dict[int, bool]:
    with open(path, encoding="utf-8") as f:
        return {s["id"]: s["match"] for s in json.load(f)}


def main():
    maps = {k: load_match(v) for k, v in FILES.items()}
    all_ids = sorted(maps["p1_mini"].keys())

    results = []
    for item_id in all_ids:
        if (
            maps["p1_mini"].get(item_id) is True
            and maps["p1_gpt41"].get(item_id) is False
            and maps["bl_mini"].get(item_id) is False
            and maps["bl_gpt41"].get(item_id) is False
        ):
            results.append(item_id)

    print(f"Found {len(results)} samples")
    print(f"IDs: {results}")

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"Saved: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
