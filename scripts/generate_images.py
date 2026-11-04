"""prompts/<name>.txt ごとに images/covers/<name>.png を1枚作る。既にある画像は作り直さない。"""
import base64
import json
import os
import pathlib
import sys
import urllib.request

MODEL = os.environ.get("IMAGE_MODEL", "gpt-image-1")
SIZE = "1024x1536"  # 縦長(インスタの4:5に近い)
QUALITY = os.environ.get("IMAGE_QUALITY", "medium")

key = os.environ.get("OPENAI_API_KEY")
if not key:
    sys.exit("OPENAI_API_KEY が GitHub の Secrets に設定されていません")

out_dir = pathlib.Path("images/covers")
out_dir.mkdir(parents=True, exist_ok=True)

for prompt_file in sorted(pathlib.Path("prompts").glob("*.txt")):
    out = out_dir / f"{prompt_file.stem}.png"
    if out.exists():
        continue
    prompt = prompt_file.read_text(encoding="utf-8").strip()
    body = json.dumps({"model": MODEL, "prompt": prompt, "size": SIZE,
                       "quality": QUALITY, "n": 1}).encode()
    req = urllib.request.Request(
        "https://api.openai.com/v1/images/generations", data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as resp:
        data = json.load(resp)
    out.write_bytes(base64.b64decode(data["data"][0]["b64_json"]))
    print(f"generated {out}")
