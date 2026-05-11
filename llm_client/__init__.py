import os
from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

_openai_api_key = os.getenv("OPENAI_API_KEY")
if not _openai_api_key:
    raise RuntimeError("OPENAI_API_KEY is missing")

_openai_client = OpenAI(api_key=_openai_api_key)
_openai_model = os.getenv("CHAT_MODEL", "gpt-4o-mini")

class OpenAIClient:
    def __init__(self):
        self._client = _openai_client
        self.model = _openai_model

    def call_llm(self, input: str, temperature: float = 0, **kwargs):
        response = self._client.responses.create(
            model=self.model,
            input=input,
            temperature=temperature,
            **kwargs
        )
        return response.output_text.strip()

    def call_llm2(self, system_prompt: str, image_b64_list: list[str], temperature: float = 0, **kwargs):
        """
        Send a system prompt (text) followed by a list of base64-encoded PNG images
        as user content.
        """
        user_content = [
            {"type": "input_image", "image_url": f"data:image/png;base64,{b64}"}
            for b64 in image_b64_list
        ]
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]

        response = self._client.responses.create(
            model=self.model,
            input=messages,
            temperature=temperature,
            **kwargs
        )
        return response.output_text.strip()