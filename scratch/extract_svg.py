import json
import re

log_path = "/Users/jihanmaisaroh/.gemini/antigravity-ide/brain/20bcd380-902e-428b-92d1-f6471fd7c175/.system_generated/logs/transcript_full.jsonl"

found_svg = None
with open(log_path, "r", encoding="utf-8") as f:
    for line in f:
        try:
            obj = json.loads(line)
            content = obj.get("content", "")
            if "summary-1" in content and "f:bg-primary/10" in content:
                # Find the SVG block: starts with <svg and ends with </svg>
                match = re.search(r'(<svg id="summary".*?</svg>)', content, re.DOTALL)
                if match:
                    found_svg = match.group(1)
                    print("Found SVG of length:", len(found_svg))
                    break
        except Exception as e:
            pass

if found_svg:
    with open("scratch/extracted_summary_svg.html", "w", encoding="utf-8") as out:
        out.write(found_svg)
    print("Successfully saved to scratch/extracted_summary_svg.html")
else:
    print("Could not find SVG block in transcript_full.jsonl")
