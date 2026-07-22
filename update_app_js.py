import re

filename = "app.js"
with open(filename, "r") as f:
    content = f.read()

# 1. Update the table header in renderSeTable
# We look for <th rowspan="2" class="sortable" onclick="sortSeTable('${surveyType}', 'delta_persen')"
header_pattern = r"<th rowspan=\"2\" class=\"sortable\" onclick=\"sortSeTable\('\$\{surveyType\}', 'delta_persen'\)\"[^>]*>[\s\S]*?Delta \(\%\)\$\{getIcon\('delta_persen'\)\}[\s\S]*?<\/th>"
new_header = """<th colspan="3" style="font-family: 'Outfit', sans-serif; text-align: center; color: var(--color-opened); border-bottom: 1px solid var(--card-border);">
                    Delta Kinerja (%)
                </th>"""
content = re.sub(header_pattern, new_header, content)

# And inject the subheaders. The subheaders end with </th>\n            </tr>\n        `;
subheader_pattern = r"Total\$\{getIcon\('total_submitted'\)\}[\s\S]*?<\/th>([\s\S]*?)<\/tr>\s*`;"
new_subheader_inject = """Total${getIcon('total_submitted')}
                </th>\\1    <th class="sortable" onclick="sortSeTable('${surveyType}', 'delta_lusa_persen')" style="font-family: 'Outfit', sans-serif; text-align: center; color: var(--text-secondary); font-size: 0.8rem; padding: 0.4rem 0.75rem; border-left: 1px solid var(--card-border);">
                    H-2${getIcon('delta_lusa_persen')}
                </th>
                <th class="sortable" onclick="sortSeTable('${surveyType}', 'delta_kemarin_persen')" style="font-family: 'Outfit', sans-serif; text-align: center; color: var(--text-secondary); font-size: 0.8rem; padding: 0.4rem 0.75rem;">
                    H-1${getIcon('delta_kemarin_persen')}
                </th>
                <th class="sortable" onclick="sortSeTable('${surveyType}', 'delta_persen')" style="font-family: 'Outfit', sans-serif; text-align: center; color: var(--primary); font-size: 0.8rem; padding: 0.4rem 0.75rem;">
                    Hari Ini${getIcon('delta_persen')}
                </th>
            </tr>
        `;"""
content = re.sub(subheader_pattern, new_subheader_inject, content)

# 2. Update the row rendering
row_pattern = r"<td style=\"text-align: center;\">\s*\$\{item\.delta_persen !== undefined && item\.delta_persen !== 0 \?[\s\S]*?<\/td>"
new_row = """<td style="text-align: center;">
                    ${item.delta_lusa_persen !== undefined && item.delta_lusa_persen !== 0 ? 
                        `<span style="font-size: 0.8rem; font-weight: 700; color: ${item.delta_lusa_persen > 0 ? '#22c55e' : (item.delta_lusa_persen < 0 ? '#ef4444' : 'inherit')};">
                            ${item.delta_lusa_persen > 0 ? '+' : ''}${item.delta_lusa_persen.toFixed(2)}%
                        </span>` 
                        : `<span style="font-size: 0.8rem; color: var(--text-muted);">-</span>`}
                </td>
                <td style="text-align: center;">
                    ${item.delta_kemarin_persen !== undefined && item.delta_kemarin_persen !== 0 ? 
                        `<span style="font-size: 0.8rem; font-weight: 700; color: ${item.delta_kemarin_persen > 0 ? '#22c55e' : (item.delta_kemarin_persen < 0 ? '#ef4444' : 'inherit')};">
                            ${item.delta_kemarin_persen > 0 ? '+' : ''}${item.delta_kemarin_persen.toFixed(2)}%
                        </span>` 
                        : `<span style="font-size: 0.8rem; color: var(--text-muted);">-</span>`}
                </td>
                <td style="text-align: center;">
                    ${item.delta_persen !== undefined && item.delta_persen !== 0 ? 
                        `<span style="font-size: 0.8rem; font-weight: 800; color: ${item.delta_persen > 0 ? '#22c55e' : (item.delta_persen < 0 ? '#ef4444' : 'inherit')};">
                            ${item.delta_persen > 0 ? '+' : ''}${item.delta_persen.toFixed(2)}%
                        </span>` 
                        : `<span style="font-size: 0.8rem; color: var(--text-muted);">-</span>`}
                </td>"""
content = re.sub(row_pattern, new_row, content)

# 3. Handle sorting for the new columns
old_sort = """                case 'delta_persen':
                    valA = parseFloat(a.delta_persen) || 0;
                    valB = parseFloat(b.delta_persen) || 0;
                    break;"""

new_sort = """                case 'delta_persen':
                    valA = parseFloat(a.delta_persen) || 0;
                    valB = parseFloat(b.delta_persen) || 0;
                    break;
                case 'delta_kemarin_persen':
                    valA = parseFloat(a.delta_kemarin_persen) || 0;
                    valB = parseFloat(b.delta_kemarin_persen) || 0;
                    break;
                case 'delta_lusa_persen':
                    valA = parseFloat(a.delta_lusa_persen) || 0;
                    valB = parseFloat(b.delta_lusa_persen) || 0;
                    break;"""

if old_sort in content:
    content = content.replace(old_sort, new_sort)
    print("Replaced old_sort")

with open(filename, "w") as f:
    f.write(content)

print("Updated app.js")

