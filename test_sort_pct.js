let arr = [
    { name: 'Riska A', pct: 0.587 },
    { name: 'Riska B', pct: 0.475 }
];

let sortOrder = 1; // Ascending
arr.sort((a, b) => {
    let valA = a.pct;
    let valB = b.pct;
    const cmp = (valA - valB) * sortOrder;
    if (cmp !== 0) return cmp;
    return a.name.localeCompare(b.name);
});

console.log(arr.map(x => x.name));
