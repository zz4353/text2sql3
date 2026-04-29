import os
import json
from utils import render_prompt, fuzzy_match


def extract_values(llm, user_request, columns: dict[str, list[str]], schema_context):
    _examples = {sc["original_column_name"]: sc["samples"] for sc in schema_context}

    n_samples = 2
    examples = [
        {
            "table": table,
            "operation": None,
            "records": [
                {
                    col: _examples[f"{table}.{col}"][i]
                    for col in col_list
                    if f"{table}.{col}" in _examples and i < len(_examples[f"{table}.{col}"])
                }
                for i in range(n_samples)
            ]
        }
        for table, col_list in columns.items()
    ]

    schema_context = [
        {k: v for k, v in sc.items() if k != "samples"}
        for sc in schema_context
    ]

    template_path = os.path.join(os.path.dirname(__file__), "templates/extract_values.md")
    prompt = render_prompt(template_path, user_input=user_request, column_descriptions=schema_context, columns=columns, examples=examples)
    llm_raw_result = llm.call_llm(prompt, text={"format": {"type": "json_object"}})
    llm_raw_result = json.loads(llm_raw_result)

    result = []
    for group in llm_raw_result.get("tables", []):
        table = group.get("table", "")
        operation = group.get("operation", None)
        candidates = tuple(columns.get(table, []))
        records = []
        for record in group.get("records", []):
            _record = {}
            for key, value in record.items():
                matched_col = fuzzy_match(key, candidates)
                if matched_col:
                    _record[matched_col] = value
            if _record:
                records.append(_record)
        if records:
            result.append({"table": table, "operation": operation, "records": records})

    return result