const fs = require('fs');

// Read and parse ipas_data.js
let rawData = fs.readFileSync('ipas_data.js', 'utf8');
let jsonStr = rawData.replace('const GLOBAL_DATABASE_NEW = ', '').trim();
if (jsonStr.endsWith(';')) jsonStr = jsonStr.slice(0, -1);

const data = JSON.parse(jsonStr);

let totalToday = 0;
let totalYesterday = 0;
let todayBreakdown = {};
let yesterdayBreakdown = {};

data.forEach(item => {
    totalToday += item.today_completed || 0;
    totalYesterday += item.yesterday_completed || 0;
    
    if (item.today_completed_breakdown) {
        for (const [status, count] of Object.entries(item.today_completed_breakdown)) {
            todayBreakdown[status] = (todayBreakdown[status] || 0) + count;
        }
    }
    if (item.yesterday_completed_breakdown) {
        for (const [status, count] of Object.entries(item.yesterday_completed_breakdown)) {
            yesterdayBreakdown[status] = (yesterdayBreakdown[status] || 0) + count;
        }
    }
});

console.log("=== TODAY ===");
console.log(`Total today_completed: ${totalToday}`);
console.log(`Raw todayBreakdown:`, todayBreakdown);
console.log(`Sum of todayBreakdown:`, Object.values(todayBreakdown).reduce((a, b) => a + b, 0));

console.log("\n=== YESTERDAY ===");
console.log(`Total yesterday_completed: ${totalYesterday}`);
console.log(`Raw yesterdayBreakdown:`, yesterdayBreakdown);
console.log(`Sum of yesterdayBreakdown:`, Object.values(yesterdayBreakdown).reduce((a, b) => a + b, 0));
