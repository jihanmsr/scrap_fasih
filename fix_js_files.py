for filename in ['fast_petugas_progress.js', 'fast_petugas_history.js', 'petugas_region_map.js']:
    try:
        with open(filename, 'r') as f:
            content = f.read()
        if content.endswith(';\\n\n') or content.endswith(';\\n'):
            content = content.replace(';\\n', ';\n')
            with open(filename, 'w') as f:
                f.write(content)
            print(f"Fixed {filename}")
    except Exception as e:
        print(e)
