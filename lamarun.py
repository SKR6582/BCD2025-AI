import requests
import json
import time
import random

def run_ollama_api(model: str, prompt: str, stream: bool = True, human_delay: bool = True):
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": model,
        "prompt": prompt
    }
    response = requests.post(url, json=payload, stream=stream)

    buffer = ""
    output = ""

    for chunk in response.iter_content(chunk_size=None):
        if chunk:
            buffer += chunk.decode("utf-8")
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                if not line.strip():
                    continue
                data = json.loads(line)
                if "response" in data:
                    token = data["response"]
                    output += token
                    print(token, end="", flush=True)

                    # 사람처럼 생각하다가 말하는 느낌으로 랜덤 딜레이
                    if human_delay:
                        time.sleep(random.uniform(0.05, 0.25))
    return output


# 예시 실행
run_ollama_api(model="gemma3:4b", prompt="",human_delay=False)