from __future__ import annotations

import os

from dotenv import load_dotenv
from langchain_nvidia_ai_endpoints import ChatNVIDIA


load_dotenv()

api_key = os.getenv("NVIDIA_API_KEY") or os.getenv("GEM29b_api_key")
if not api_key:
    raise RuntimeError("Set NVIDIA_API_KEY or GEM29b_api_key in .env before running this script.")

client = ChatNVIDIA(
    model="google/gemma-2-9b-it",
    api_key=api_key,
    temperature=0.2,
    top_p=0.7,
    max_completion_tokens=1024,
)

for chunk in client.stream([{"role": "user", "content": "Hello. Please answer in one short sentence."}]):
    print(chunk.content, end="")
