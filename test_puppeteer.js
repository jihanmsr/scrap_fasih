const puppeteer = require('puppeteer');
(async () => {
    const browser = await puppeteer.launch({ args: ['--no-sandbox', '--disable-setuid-sandbox'] });
    const page = await browser.newPage();
    page.on('console', msg => console.log('PAGE LOG:', msg.text()));
    page.on('pageerror', err => console.log('PAGE ERROR:', err.message));
    page.on('requestfailed', request => console.log('REQUEST FAILED:', request.url(), request.failure().errorText));
    await page.goto('https://taskforce.bpssulteng.id', { waitUntil: 'networkidle2' });
    await new Promise(r => setTimeout(r, 5000));
    console.log("se_umum prelist HTML:", await page.$eval('#se_umum-stat-total-prelist', el => el.textContent).catch(e => e.message));
    console.log("IPAS_DATA:", await page.evaluate(() => window.IPAS_DATA ? "YES" : "NO"));
    await browser.close();
})();
