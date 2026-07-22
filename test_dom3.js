const jsdom = require("jsdom");
const { JSDOM } = jsdom;

JSDOM.fromURL("https://taskforce.bpssulteng.id", {
    runScripts: "dangerously",
    resources: "usable"
}).then(dom => {
    setTimeout(() => {
        const el = dom.window.document.getElementById('se_umum-stat-total-prelist');
        console.log("Total Target text:", el ? el.textContent : "null");
        if (dom.window.IPAS_DATA) {
            console.log("se_umum prelist from data:", dom.window.IPAS_DATA.se_umum?.[0]?.total_prelist);
        } else {
            console.log("IPAS_DATA is undefined");
        }
    }, 10000);
}).catch(e => console.error(e));
