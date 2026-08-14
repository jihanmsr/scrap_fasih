const fs = require('fs');
const js = fs.readFileSync('/Users/jihanmaisaroh/scrap_fasih/open_subsls.js', 'utf8');
try {
  new Function(js);
  console.log("Syntax is valid");
} catch(e) {
  console.log("Error:", e);
}
