const puppeteer = require('puppeteer');
const path = require('path');

(async () => {
    const browser = await puppeteer.launch({
        headless: "new",
        args: ['--no-sandbox', '--disable-setuid-sandbox', '--font-render-hinting=none']
    });
    const page = await browser.newPage();

    // Set viewport to a high resolution
    await page.setViewport({ width: 1920, height: 1080, deviceScaleFactor: 2 });

    const fileUrl = 'file://' + path.resolve('temp_diagram.html');
    console.log('Navigating to:', fileUrl);
    await page.goto(fileUrl, { waitUntil: 'networkidle0' });

    // Wait for mermaid to render
    await page.waitForSelector('.mermaid svg');

    // Select the container
    const element = await page.$('#diagram-container');

    if (element) {
        const outputPath = path.resolve('assets/k8s_network_architecture.png');
        await element.screenshot({ path: outputPath, omitBackground: true });
        console.log(`Screenshot saved to ${outputPath}`);
    } else {
        console.error('Element #diagram-container not found');
    }

    await browser.close();
})();
