from langchain_nvidia_ai_endpoints import ChatNVIDIA
from dotenv import load_dotenv
import os
load_dotenv()

api_key = os.getenv("openai_api_key")

client = ChatNVIDIA(
  model="openai/gpt-oss-120b",
  api_key=api_key,
  temperature=1,
  top_p=1,
  max_tokens=4096,
)

for chunk in client.stream([{"role":"user","content":""}]):
  if chunk.additional_kwargs and "reasoning_content" in chunk.additional_kwargs:
    print(chunk.additional_kwargs["reasoning_content"], end="")
  print(chunk.content, end="")