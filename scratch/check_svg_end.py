import json

log_path = "/Users/jihanmaisaroh/.gemini/antigravity-ide/brain/20bcd380-902e-428b-92d1-f6471fd7c175/.system_generated/logs/transcript_full.jsonl"

with open(log_path, "r", encoding="utf-8") as f:
    for idx, line in enumerate(f):
        if idx == 840:
            obj = json.loads(line)
            content = obj.get("content", "")
            print("Content length:", len(content))
            print("Ends with:", content[-100:])
            print("Contains </svg>:", "</svg>" in content)
            print("Contains <svg>:", "<svg" in content)
