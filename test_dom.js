const fs = require('fs');
const jsdom = require("jsdom");
const { JSDOM } = jsdom;

const html = fs.readFileSync('index.html', 'utf8');

const dom = new JSDOM(html, {
    url: "file:///Users/jihanmaisaroh/scrap_fasih/index.html",
    runScripts: "dangerously",
    resources: "usable"
});

dom.window.addEventListener("load", () => {
    setTimeout(() => {
        console.log("window.IPAS_DATA loaded:", !!dom.window.IPAS_DATA);
        if (dom.window.IPAS_DATA) {
            console.log("se_umum length:", dom.window.IPAS_DATA.se_umum.length);
        }
        console.log("Total Target text:", dom.window.document.getElementById('se_umum-stat-total-prelist').textContent);
    }, 2000);
});
