import os
import json
from db_client import get_database_schema, DB_ID
from utils import render_prompt
from llm_client import OpenAIClient

llm = OpenAIClient()

def run_baseline(db_id: DB_ID, user_request):
    template_path = os.path.join(os.path.dirname(__file__), "templates/prompt.md")
    schema_context = get_database_schema(db_id)
    prompt = render_prompt(template_path, schema=schema_context, user_input=user_request)
    llm_raw_result = llm.call_llm(prompt, text={"format": {"type": "json_object"}})
    llm_raw_result = json.loads(llm_raw_result)['sqls']

    return llm_raw_result