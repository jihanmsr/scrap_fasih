const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({headless: "new"});
  const page = await browser.newPage();
  page.on('console', msg => console.log('PAGE LOG:', msg.text()));
  page.on('pageerror', err => console.log('PAGE ERROR:', err.toString()));
  await page.goto('file://' + process.cwd() + '/index.html', { waitUntil: 'networkidle0' });
  
  const text = await page.evaluate(() => {
    return document.getElementById('se_umum-stat-total-prelist-wrapper').innerText;
  });
  console.log('SE UMUM WRAPPER:', text);
  
  await browser.close();
})();
