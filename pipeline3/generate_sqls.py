import os
import json
from db_client import DB_ID, get_all_foreign_keys
from utils import render_prompt


def generate_sqls(db_id: DB_ID, llm, user_request, columns: dict[str, list[str]], schema_context) -> list[str]:
    template_path = os.path.join(os.path.dirname(__file__), "templates/generate_sqls.md")
    foreign_keys = get_all_foreign_keys(db_id)
    selected_schema = _filter_schema(schema_context, columns)

    prompt = render_prompt(
        template_path,
        user_input=user_request,
        columns=columns,
        schema=selected_schema,
        foreign_keys=foreign_keys,
    )

    raw = llm.call_llm(prompt, text={"format": {"type": "json_object"}})
    return json.loads(raw).get("sql", [])


def _filter_schema(schema_context, columns: dict[str, list[str]]) -> list:
    selected = {f"{table}.{col}" for table, cols in columns.items() for col in cols}
    return [sc for sc in schema_context if sc.get("original_column_name") in selected]
