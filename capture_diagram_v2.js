const puppeteer = require('puppeteer');
const path = require('path');

(async () => {
    console.log('Launching browser...');
    const browser = await puppeteer.launch({
        headless: "new",
        args: ['--no-sandbox', '--disable-setuid-sandbox', '--font-render-hinting=none']
    });
    const page = await browser.newPage();

    // Set viewport to 4k resolution with high pixel density (3x)
    const width = 3840;
    const height = 2160;
    const deviceScaleFactor = 3;
    await page.setViewport({ width, height, deviceScaleFactor });
    console.log(`Viewport set to ${width}x${height} @ ${deviceScaleFactor}x`);

    const fileUrl = 'file://' + path.resolve('temp_diagram.html');
    console.log('Navigating to:', fileUrl);

    // Wait for network idle to ensure FontAwesome loads
    await page.goto(fileUrl, { waitUntil: 'networkidle0' });

    // Explicitly wait for mermaid diagram to be present
    console.log('Waiting for .mermaid svg selector...');
    await page.waitForSelector('.mermaid svg', { timeout: 10000 });

    // Wait a bit more for fonts to settle/render
    await new Promise(r => setTimeout(r, 2000));

    // Select the container
    const element = await page.$('#diagram-container');

    if (element) {
        const outputPath = path.resolve('assets/k8s_network_architecture.png');
        console.log(`Capturing screenshot to ${outputPath}...`);
        await element.screenshot({ path: outputPath, omitBackground: true });
        console.log('Screenshot saved successfully.');
    } else {
        console.error('Element #diagram-container not found');
        process.exit(1);
    }

    await browser.close();
    console.log('Browser closed.');
})();
