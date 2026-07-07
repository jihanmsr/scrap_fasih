import json

log_path = "/Users/jihanmaisaroh/.gemini/antigravity-ide/brain/20bcd380-902e-428b-92d1-f6471fd7c175/.system_generated/logs/transcript.jsonl"
with open(log_path, "r", encoding="utf-8") as f:
    for line in f:
        try:
            obj = json.loads(line)
            content = obj.get("content", "")
            if "summary-1" in content and "f:bg-primary/10" in content:
                print("Found match in step:", obj.get("step_index"))
                # Print only the first 2000 characters of content to avoid flooding
                print(content[:2000])
                print("\n" + "="*40 + "\n")
        except Exception as e:
            pass
