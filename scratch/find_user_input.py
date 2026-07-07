import json

log_path = "/Users/jihanmaisaroh/.gemini/antigravity-ide/brain/20bcd380-902e-428b-92d1-f6471fd7c175/.system_generated/logs/transcript_full.jsonl"

with open(log_path, "r", encoding="utf-8") as f:
    for idx, line in enumerate(f):
        if "summary-1" in line:
            obj = json.loads(line)
            print(f"Line {idx}: type={obj.get('type')}, keys={list(obj.keys())}")
            # Print a snippet of content
            c = obj.get("content", "")
            if isinstance(c, str):
                print("Content length:", len(c))
                print(c[:200])
            else:
                print("Content type is:", type(c))
            print("="*50)
