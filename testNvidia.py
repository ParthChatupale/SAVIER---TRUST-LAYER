from langchain_nvidia_ai_endpoints import ChatNVIDIA
from dotenv import load_dotenv
import os
load_dotenv()

key = os.getenv("GEM29b_api_key")

if key:
    print(f"Key loaded! Length: {len(key)}")
    print(f"Starts with: '{key[:5]}'") # Check for unexpected spaces at the start
else:
    print("Error: Could not find 'GEM29b_api_key' in environment.")

api_key = os.getenv("GEM29b_api_key")
client = ChatNVIDIA(
  model="google/gemma-2-9b-it",
  api_key=api_key,
  temperature=0.2,
  top_p=0.7,
  max_tokens=1024,
)

for chunk in client.stream([{"role":"user","content":"Hello How are you please answer"}]): 
  print(chunk.content, end="")



