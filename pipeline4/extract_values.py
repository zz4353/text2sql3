import os
import json
from utils import render_prompt, fuzzy_match
from utils.text_to_image import render_text_pages_b64


def extract_values(llm, user_request, columns: dict[str, list[str]], schema_context):
    examples = _build_examples(columns, schema_context)
    schema_context_stripped = _strip_samples(schema_context)
    llm_raw_result = _call_extract_llm(llm, user_request, columns, schema_context_stripped, examples)
    return _parse_llm_records(llm_raw_result, columns)

def _build_examples(columns: dict[str, list[str]], schema_context, n_samples: int = 2) -> list:
    _examples = {sc["original_column_name"]: sc["samples"] for sc in schema_context}
    return [
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


def _strip_samples(schema_context) -> list:
    return [{k: v for k, v in sc.items() if k != "samples"} for sc in schema_context]


def _call_extract_llm(llm, user_request, columns, schema_context_stripped, examples) -> dict:
    template_path = os.path.join(os.path.dirname(__file__), "templates/extract_values.md")
    system_prompt = render_prompt(template_path, columns=columns, examples=examples)

    schema_text = _format_column_descriptions(schema_context_stripped)
    schema_images = render_text_pages_b64(schema_text, header="[Column Descriptions]")
    user_input_images = render_text_pages_b64(str(user_request), header="[User Request]")
    all_images = schema_images + user_input_images

    raw = llm.call_llm2(system_prompt, all_images, text={"format": {"type": "json_object"}})
    return json.loads(raw)


def _format_column_descriptions(schema_context_stripped: list[dict]) -> str:
    return "\n\n".join(json.dumps(col, ensure_ascii=False) for col in schema_context_stripped)


def _parse_llm_records(llm_result: dict, columns: dict[str, list[str]]) -> list:
    result = []
    for group in llm_result.get("tables", []):
        table = group.get("table", "")
        if table not in columns:
            table = fuzzy_match(table, tuple(columns), cutoff=0.8)
            if not table:
                continue

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
