import re

with open('index.html', 'r') as f:
    html = f.read()

# Remove all newly added Kabkot dropdowns to reset
html = re.sub(r'<!-- Dropdown Filter Kabkot -->.*?</select>', '', html, flags=re.DOTALL)

# Insert clean ones
dropdown_umum = """<!-- Dropdown Filter Kabkot -->
                            <select class="sort-select" id="se_umum-kab-filter" onchange="window.filterSeTableByKab('se_umum')"
                                style="height: 38px; font-family: 'Outfit', sans-serif; font-size: 0.85rem; font-weight: 600; padding: 0 2rem 0 0.75rem; border-radius: 0.5rem; border: 1px solid var(--card-border); background: var(--input-bg) url('data:image/svg+xml;charset=US-ASCII,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%22292.4%22%20height%3D%22292.4%22%3E%3Cpath%20fill%3D%22%23a0aec0%22%20d%3D%22M287%2069.4a17.6%2017.6%200%200%200-13-5.4H18.4c-5%200-9.3%201.8-12.9%205.4A17.6%2017.6%200%200%200%200%2082.2c0%205%201.8%209.3%205.4%2012.9l128%20127.9c3.6%203.6%207.8%205.4%2012.8%205.4s9.2-1.8%2012.8-5.4L287%2095c3.5-3.5%205.4-7.8%205.4-12.8%200-5-1.9-9.2-5.5-12.8z%22%2F%3E%3C%2Fsvg%3E') no-repeat right 0.75rem center; background-size: 0.65em auto; color: var(--text-primary); cursor: pointer; outline: none; -webkit-appearance: none; -moz-appearance: none; appearance: none; min-width: 180px;">
                                <option value="all">Semua Kabupaten/Kota</option>
                            </select>"""

dropdown_ub = """<!-- Dropdown Filter Kabkot -->
                            <select class="sort-select" id="se_ub-kab-filter" onchange="window.filterSeTableByKab('se_ub')"
                                style="height: 38px; font-family: 'Outfit', sans-serif; font-size: 0.85rem; font-weight: 600; padding: 0 2rem 0 0.75rem; border-radius: 0.5rem; border: 1px solid var(--card-border); background: var(--input-bg) url('data:image/svg+xml;charset=US-ASCII,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%22292.4%22%20height%3D%22292.4%22%3E%3Cpath%20fill%3D%22%23a0aec0%22%20d%3D%22M287%2069.4a17.6%2017.6%200%200%200-13-5.4H18.4c-5%200-9.3%201.8-12.9%205.4A17.6%2017.6%200%200%200%200%2082.2c0%205%201.8%209.3%205.4%2012.9l128%20127.9c3.6%203.6%207.8%205.4%2012.8%205.4s9.2-1.8%2012.8-5.4L287%2095c3.5-3.5%205.4-7.8%205.4-12.8%200-5-1.9-9.2-5.5-12.8z%22%2F%3E%3C%2Fsvg%3E') no-repeat right 0.75rem center; background-size: 0.65em auto; color: var(--text-primary); cursor: pointer; outline: none; -webkit-appearance: none; -moz-appearance: none; appearance: none; min-width: 180px;">
                                <option value="all">Semua Kabupaten/Kota</option>
                            </select>"""

# Replace first occurrence
html = html.replace('<!-- Dropdown Filter Capaian -->', dropdown_umum + '\n                            <!-- Dropdown Filter Capaian -->', 1)

# Replace second occurrence
parts = html.split('<!-- Dropdown Filter Capaian -->')
if len(parts) == 3:
    html = parts[0] + '<!-- Dropdown Filter Capaian -->' + parts[1] + dropdown_ub + '\n                            <!-- Dropdown Filter Capaian -->' + parts[2]

with open('index.html', 'w') as f:
    f.write(html)
