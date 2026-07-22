import sys

filename = "app.js"
with open(filename, "r") as f:
    content = f.read()

old_func = """    window.sortPetugasSummary = function (field) {
        if (window.petugasSortField === field) {
            window.petugasSortOrder *= -1;
        } else {
            window.petugasSortField = field;
            window.petugasSortOrder = field === 'name' ? 1 : -1;
        }
        const dataToRender = window.lastBaseFiltered || window.GRANULAR_ASSIGNMENTS_DATA || null;
        if (dataToRender && window.renderPetugasSummaryTable) {
            window.renderPetugasSummaryTable(dataToRender);
        }
    };"""

new_func = """    window.sortPetugasSummary = function (field) {
        if (window.petugasSortField === field) {
            window.petugasSortOrder *= -1;
        } else {
            window.petugasSortField = field;
            window.petugasSortOrder = field === 'name' ? 1 : -1;
        }
        window.petugasSummaryCurrentPage = 1;
        if (window.renderPetugasSummaryTable) {
            window.renderPetugasSummaryTable(window.lastBaseFiltered || window.GRANULAR_ASSIGNMENTS_DATA || []);
        }
    };"""

content = content.replace(old_func, new_func)

with open(filename, "w") as f:
    f.write(content)
print("Fixed sortPetugasSummary")
