const { chromium } = require('playwright');

(async () => {
    const browser = await chromium.launch();
    const page = await browser.newPage();
    
    await page.goto('http://localhost:8080/organelle_gallery.html');
    await page.waitForTimeout(3000); // Wait for Three.js to render
    
    await page.screenshot({ path: 'screenshot_gallery.png', fullPage: true });
    console.log('Screenshot saved: screenshot_gallery.png');
    
    await browser.close();
})();
