const puppeteer = require('puppeteer');

(async () => {
  const url = 'http://localhost:4173';
  console.log(`Launching headless browser to inspect ${url}...`);
  const browser = await puppeteer.launch();
  const page = await browser.newPage();
  
  const consoleErrors = [];
  const consoleLogs = [];
  
  page.on('console', msg => {
    consoleLogs.push(`[${msg.type().toUpperCase()}] ${msg.text()}`);
  });
  page.on('pageerror', err => {
    consoleErrors.push(err.toString());
  });

  try {
    await page.goto(url, { waitUntil: 'networkidle2' });
    
    // Wait a bit
    await new Promise(r => setTimeout(r, 2000));
    
    const analysis = await page.evaluate(() => {
      const getPresence = (selector) => {
        const el = document.querySelector(selector);
        return {
          exists: !!el,
          text: el ? el.innerText.substring(0, 100).replace(/\n/g, ' ') : null,
          classes: el ? Array.from(el.classList).join(' ') : null
        };
      };
      
      const findCardByHeader = (keyword) => {
        const headers = Array.from(document.querySelectorAll('h2'));
        const matchingHeader = headers.find(h => h.innerText.toLowerCase().includes(keyword.toLowerCase()));
        if (!matchingHeader) return null;
        const card = matchingHeader.closest('.glass-card') || matchingHeader.closest('section') || matchingHeader.parentElement;
        return {
          exists: true,
          headerText: matchingHeader.innerText,
          cardClasses: card ? Array.from(card.classList).join(' ') : null,
          cardTextPreview: card ? card.innerText.substring(0, 150).replace(/\n/g, ' ') : null
        };
      };

      const mlBadges = Array.from(document.querySelectorAll('.panel-badge'))
        .filter(el => el.innerText.toLowerCase().includes('ml'))
        .map(el => el.innerText);

      const freshnessTable = document.querySelector('.freshness-table') || document.querySelector('table');

      return {
        title: document.title,
        header: getPresence('header'),
        citySelector: getPresence('.city-selector') || getPresence('.city-tabs') || getPresence('select'),
        statusIndicator: getPresence('.header-right') || getPresence('.status-dot'),
        mainGrid: getPresence('main.dashboard-grid'),
        cardsCount: document.querySelectorAll('.ewi-card').length,
        
        // Cards
        riskBarometer: findCardByHeader('risikobarometer') || findCardByHeader('risk'),
        priceIndexPanel: findCardByHeader('prisindeks'),
        earlyWarningDashboard: findCardByHeader('tidlig varsling') || findCardByHeader('ewi'),
        forecastPanel: findCardByHeader('prisprognose') || findCardByHeader('prognose'),
        userCostPanel: findCardByHeader('brugeromkostninger') || findCardByHeader('user cost'),
        scenarioPanel: findCardByHeader('scenarie'),
        
        mlBadges: mlBadges,
        freshnessTable: freshnessTable ? {
          exists: true,
          htmlPreview: freshnessTable.outerHTML.substring(0, 300).replace(/\n/g, ' '),
          textPreview: freshnessTable.innerText.substring(0, 150).replace(/\n/g, ' ')
        } : { exists: false },
        
        allH2s: Array.from(document.querySelectorAll('h2')).map(el => el.innerText),
        bodyHtmlLength: document.body.innerHTML.length
      };
    });

    console.log("\n=== CONSOLE LOGS ===");
    consoleLogs.forEach(log => console.log(log));
    
    console.log("\n=== CONSOLE ERRORS ===");
    if (consoleErrors.length === 0) {
      console.log("NONE");
    } else {
      consoleErrors.forEach(err => console.error(err));
    }
    
    console.log("\n=== DOM ANALYSIS ===");
    console.log(JSON.stringify(analysis, null, 2));

  } catch (error) {
    console.error("Failed to run check:", error);
  } finally {
    await browser.close();
    console.log("Browser closed.");
  }
})();
