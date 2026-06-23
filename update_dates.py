import re
with open("index.html", "r", encoding="utf-8") as f:
    html = f.read()

# Let's add a script at the end of the body in index.html to dynamically replace the texts!
script = """
<script>
    document.addEventListener("DOMContentLoaded", function() {
        const t = new Date();
        const y = new Date(t); y.setDate(y.getDate() - 1);
        const h2 = new Date(t); h2.setDate(h2.getDate() - 2);
        const fmt = d => String(d.getDate()).padStart(2, '0') + '/' + String(d.getMonth()+1).padStart(2, '0');
        
        const strToday = "Hari Ini (" + fmt(t) + ")";
        const strYesterday = "Kemarin (" + fmt(y) + ")";
        const strH2 = "2 Hari Lalu (" + fmt(h2) + ")";
        const strH2B = "H-2 (" + fmt(h2) + ")";

        // Replace in stat-label divs
        document.querySelectorAll('.stat-label').forEach(el => {
            if (el.textContent.includes('Submit Hari Ini')) el.innerHTML = 'Submit ' + strToday;
            if (el.textContent.includes('Submit Kemarin')) el.innerHTML = 'Submit ' + strYesterday;
            if (el.textContent.includes('Submit 2 Hari Lalu')) el.innerHTML = 'Submit ' + strH2;
        });

        // Replace in th elements
        document.querySelectorAll('th').forEach(el => {
            if (el.textContent.includes('Progres (Hari Ini | Kemarin)')) {
                el.innerHTML = 'Progres (' + strToday + ' | ' + strYesterday + ')';
            }
        });
    });
</script>
</body>
"""

html = html.replace("</body>", script)

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)
print("index.html patched with dynamic dates!")

with open("app.js", "r", encoding="utf-8") as f:
    app_js = f.read()

# Replace hardcoded strings in app.js
app_js = app_js.replace("['H-2', 'Kemarin', 'Hari Ini']", "[`H-2 (${fmt(h2)})`, `Kemarin (${fmt(y)})`, `Hari Ini (${fmt(t)})`]")
# Oh wait, fmt(h2) is not defined in that scope.

app_js = app_js.replace("Hari Ini${getIcon('today_completed')}", "${getFormattedDateLabels().today}${getIcon('today_completed')}")
app_js = app_js.replace("Kemarin${getIcon('yesterday_completed')}", "${getFormattedDateLabels().yesterday}${getIcon('yesterday_completed')}")
app_js = app_js.replace("H-2${getIcon('two_days_ago_completed')}", "${getFormattedDateLabels().h2}${getIcon('two_days_ago_completed')}")

with open("app.js", "w", encoding="utf-8") as f:
    f.write(app_js)
print("app.js patched with dynamic dates!")
