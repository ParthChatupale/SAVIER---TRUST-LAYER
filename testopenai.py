from __future__ import annotations

import os

from dotenv import load_dotenv
from langchain_nvidia_ai_endpoints import ChatNVIDIA


load_dotenv()

api_key = os.getenv("NVIDIA_API_KEY") or os.getenv("openai_api_key")
if not api_key:
    raise RuntimeError("Set NVIDIA_API_KEY or openai_api_key in .env before running this script.")

client = ChatNVIDIA(
    model="openai/gpt-oss-120b",
    api_key=api_key,
    temperature=0.2,
    top_p=0.7,
    max_completion_tokens=2048,
)

for chunk in client.stream([{"role": "user", "content": "Say hello in one short sentence."}]):
    if chunk.additional_kwargs and "reasoning_content" in chunk.additional_kwargs:
        print(chunk.additional_kwargs["reasoning_content"], end="")
    print(chunk.content, end="")
