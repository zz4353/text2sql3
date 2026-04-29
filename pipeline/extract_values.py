import os
import json
from utils import render_prompt, fuzzy_match


def extract_values(llm, user_request, columns, schema_context):
    _examples = {sc["original_column_name"]: sc["samples"] for sc in schema_context}

    # Group columns by table
    tables: dict[str, list[str]] = {}
    for col in columns:
        table, _ = col.split('.', 1)
        tables.setdefault(table, []).append(col)

    # Build examples grouped by table (columns without table prefix inside records)
    n_samples = 2
    examples = [
        {
            "table": table,
            "operation": None,
            "records": [
                {col.split('.', 1)[1]: _examples[col][i] for col in table_cols if col in _examples and i < len(_examples[col])}
                for i in range(n_samples)
            ]
        }
        for table, table_cols in tables.items()
    ]

    schema_context = [
        {k: v for k, v in sc.items() if k != "samples"}
        for sc in schema_context
    ]

    template_path = os.path.join(os.path.dirname(__file__), "templates/extract_values.md")
    prompt = render_prompt(template_path, user_input=user_request, column_descriptions=schema_context, columns=columns, examples=examples)
    print(prompt)
    llm_raw_result = llm.call_llm(prompt, text={"format": {"type": "json_object"}})
    llm_raw_result = json.loads(llm_raw_result)

    result = []
    for group in llm_raw_result.get("tables", []):
        table = group.get("table", "")
        operation = group.get("operation", None)
        records = []
        for record in group.get("records", []):
            _record = {}
            for key, value in record.items():
                matched_col = fuzzy_match(f"{table}.{key}", columns)
                if matched_col:
                    _record[matched_col] = value
            if _record:
                records.append(_record)
        if records:
            result.append({"table": table, "operation": operation, "records": records})

    return result