const puppeteer = require('puppeteer');

(async () => {
  const url = 'http://localhost:4173';
  console.log(`Launching headless browser to test all cities via dropdown on ${url}...`);
  const browser = await puppeteer.launch();
  const page = await browser.newPage();
  
  await page.goto(url, { waitUntil: 'networkidle2' });
  await new Promise(r => setTimeout(r, 2000));
  
  const cities = [
    { label: 'København', val: 'copenhagen' },
    { label: 'Aarhus', val: 'aarhus' },
    { label: 'Odense', val: 'odense' },
    { label: 'Aalborg', val: 'aalborg' }
  ];
  
  const results = {};
  
  for (const city of cities) {
    console.log(`Selecting city: ${city.label} (${city.val})...`);
    
    // Change select value and trigger change event
    await page.evaluate((cityVal) => {
      const select = document.querySelector('.city-selector select');
      if (select) {
        select.value = cityVal;
        select.dispatchEvent(new Event('change', { bubbles: true }));
      } else {
        console.log('City select dropdown not found!');
      }
    }, city.val);
    
    // Wait for the state to transition
    await new Promise(r => setTimeout(r, 1000));
    
    // Read state
    const state = await page.evaluate(() => {
      const badges = Array.from(document.querySelectorAll('.panel-badge'));
      const mlBadge = badges.find(el => el.innerText.toLowerCase().includes('ml'));
      const activeHeader = document.querySelector('.panel-wide h2')?.innerText || 'Unknown';
      return {
        activeCityHeader: activeHeader,
        mlBadgeText: mlBadge ? mlBadge.innerText : 'MISSING',
        ewiCardsCount: document.querySelectorAll('.ewi-card').length,
        allBadges: badges.map(el => el.innerText)
      };
    });
    
    results[city.label] = state;
  }
  
  console.log(JSON.stringify(results, null, 2));
  await browser.close();
})();
