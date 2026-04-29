import os
import json
from utils import render_prompt, fuzzy_match


def extract_values(llm, user_request, columns, schema_context):
    _examples = {sc["original_column_name"] : sc["samples"] for sc in schema_context}
    examples = [
        {col: _examples[col][i] for col in columns}
        for i in range(2)
    ]

    schema_context = [
        {k: v for k, v in sc.items() if k != "samples"}
        for sc in schema_context
    ]

    template_path = os.path.join(os.path.dirname(__file__), "templates/extract_values.md")
    prompt = render_prompt(template_path, user_input=user_request, column_descriptions=schema_context, columns=columns, examples=examples)
    llm_raw_result = llm.call_llm(prompt, text={"format": {"type": "json_object"}})
    llm_raw_result = json.loads(llm_raw_result)
    operation = llm_raw_result.get('operation', None)

    llm_result = []
    for record in llm_raw_result['records']:
        _record = {}
        for key, value in record.items():
            matched_col = fuzzy_match(key, columns)
            if matched_col:
                _record[matched_col] = value
        if _record:
            llm_result.append(_record)

    return llm_result, operation