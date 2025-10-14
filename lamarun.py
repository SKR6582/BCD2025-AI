import requests
import json

def run_ollama_api(model: str, prompt: str, stream: bool = True):
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
                    token = data["response"]   # 실제 토큰 단위
                    output += token
                    print(token, end="", flush=True)
    return output