import re

def update_timestamp(file_path, new_timestamp):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace the timestamp pattern
    new_content = re.sub(r'"timestamp":\s*"[^"]+"', f'"timestamp": "{new_timestamp}"', content)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f"Updated timestamp in {file_path}")

new_timestamp = "2026-08-10T14:06:00.000000"
update_timestamp('fast_master_assign_data.js', new_timestamp)
update_timestamp('assign_data.js', new_timestamp)
