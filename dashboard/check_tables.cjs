const puppeteer = require('puppeteer');

(async () => {
  const url = 'https://cph-housing-model.vercel.app';
  console.log(`Launching browser to inspect ${url}...`);
  const browser = await puppeteer.launch();
  const page = await browser.newPage();
  
  await page.goto(url, { waitUntil: 'networkidle2' });
  await new Promise(r => setTimeout(r, 2000));
  
  const content = await page.evaluate(() => {
    const panels = Array.from(document.querySelectorAll('.glass-card'));
    return panels.map(p => ({
      h2: p.querySelector('h2')?.innerText || 'No H2',
      htmlPreview: p.innerHTML.substring(0, 500).replace(/\n/g, ' '),
      hasTable: !!p.querySelector('table'),
      tableClass: p.querySelector('table') ? p.querySelector('table').className : null,
      tableText: p.querySelector('table') ? p.querySelector('table').innerText.substring(0, 100) : null
    }));
  });
  
  console.log(JSON.stringify(content, null, 2));
  await browser.close();
})();
