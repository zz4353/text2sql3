import json

PIPELINE1_EVAL = [
    "results/pipeline1/evaluation_gpt41.json",
    "results/pipeline1/evaluation.json",
]
BASELINE_EVAL = [
    "results/baseline/evaluation.json",
    "results/baseline/evaluation_gpt41.json",
]
OUTPUT_PATH = "results/pipeline1_wins.json"


def load_match(path) -> dict[int, bool]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return {s["id"]: s["match"] for s in data}


def main():
    p1_maps = [load_match(p) for p in PIPELINE1_EVAL]
    bl_maps = [load_match(p) for p in BASELINE_EVAL]

    all_ids = set(p1_maps[0].keys())

    results = []
    for item_id in sorted(all_ids):
        p1_correct = all(m.get(item_id) is True for m in p1_maps)
        bl_wrong = all(m.get(item_id) is False for m in bl_maps)
        if p1_correct and bl_wrong:
            results.append(item_id)

    print(f"Found {len(results)} samples: pipeline1 correct in both, baseline wrong in both")
    print(f"IDs: {results}")

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"Saved: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
