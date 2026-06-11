with open('/Users/jihanmaisaroh/scrap_fasih/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Replace inline CSS style block
style_start_marker = "<!-- Vanilla CSS Styles -->"
style_end_marker = "</style>\n</head>"

style_start_idx = content.find(style_start_marker)
style_end_idx = content.find(style_end_marker)

if style_start_idx != -1 and style_end_idx != -1:
    style_end_idx += len(style_end_marker) - len("\n</head>")
    content = content[:style_start_idx] + '<link rel="stylesheet" href="style.css">' + content[style_end_idx:]
    print("Replaced CSS style block successfully!")
else:
    print("Failed to find CSS markers!")

# 2. Replace inline JS script block
js_start_marker = "<script>\n        document.addEventListener('DOMContentLoaded', () => {"
js_end_marker = "    </script>\n    <!-- Interactive Business Details Modal -->"

js_start_idx = content.find(js_start_marker)
js_end_idx = content.find(js_end_marker)

if js_start_idx != -1 and js_end_idx != -1:
    js_end_idx += len(js_end_marker) - len("\n    <!-- Interactive Business Details Modal -->")
    content = content[:js_start_idx] + '<script src="app.js"></script>' + content[js_end_idx:]
    print("Replaced JS script block successfully!")
else:
    print("Failed to find JS markers!")

# 3. Remove duplicate header in se_umum
se_umum_header = """                <!-- Welcome Section -->
                <div
                    style="display: flex; justify-content: space-between; align-items: flex-end; gap: 1rem; margin-bottom: 2rem; flex-wrap: wrap;">
                    <div>
                        <h2
                            style="font-family: 'Outfit', sans-serif; font-size: 1.75rem; font-weight: 800; margin-bottom: 0.25rem;">
                            Analitik <span
                                style="background: linear-gradient(to right, #60a5fa, #a78bfa); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Progres
                                Harian</span> (Semua Usaha)</h2>
                        <p style="color: var(--text-secondary); font-size: 0.9rem;">Pemantauan penyelesaian Sensus
                            Ekonomi
                            2026 di Sulawesi Tengah</p>
                    </div>
                    <div>
                        <div
                            style="background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.2); padding: 0.5rem 1rem; border-radius: 0.75rem; display: flex; align-items: center; gap: 0.5rem;">
                            <span
                                style="width: 8px; height: 8px; border-radius: 50%; background-color: #10b981; display: inline-block; animation: pulse 2s infinite;"></span>
                            <span style="font-size: 0.75rem; font-weight: 700; color: #10b981;">LIVE SYNC ACTIVE</span>
                        </div>
                    </div>
                </div>"""

if se_umum_header in content:
    content = content.replace(se_umum_header, "")
    print("Removed duplicate se_umum header successfully!")
else:
    # Try normalized spacing
    normalized_header = "\n".join(line.strip() for line in se_umum_header.split("\n"))
    print("se_umum header not found with exact spacing, trying custom strip logic")

# 4. Remove duplicate header in se_ub
se_ub_header = """                <!-- Welcome Section -->
                <div
                    style="display: flex; justify-content: space-between; align-items: flex-end; gap: 1rem; margin-bottom: 2rem; flex-wrap: wrap;">
                    <div>
                        <h2
                            style="font-family: 'Outfit', sans-serif; font-size: 1.75rem; font-weight: 800; margin-bottom: 0.25rem;">
                            Analitik <span
                                style="background: linear-gradient(to right, #60a5fa, #a78bfa); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Progres
                                Harian</span> (UB)</h2>
                        <p style="color: var(--text-secondary); font-size: 0.9rem;">Pemantauan penyelesaian Sensus
                            Ekonomi
                            2026 - UB di Sulawesi Tengah</p>
                    </div>
                    <div>
                        <div
                            style="background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.2); padding: 0.5rem 1rem; border-radius: 0.75rem; display: flex; align-items: center; gap: 0.5rem;">
                            <span
                                style="width: 8px; height: 8px; border-radius: 50%; background-color: #10b981; display: inline-block; animation: pulse 2s infinite;"></span>
                            <span style="font-size: 0.75rem; font-weight: 700; color: #10b981;">LIVE SYNC ACTIVE</span>
                        </div>
                    </div>
                </div>"""

if se_ub_header in content:
    content = content.replace(se_ub_header, "")
    print("Removed duplicate se_ub header successfully!")
else:
    print("se_ub header not found with exact spacing!")

with open('/Users/jihanmaisaroh/scrap_fasih/index.html', 'w', encoding='utf-8') as f:
    f.write(content)
