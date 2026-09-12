const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage();
  await p.goto('file://' + __dirname + '/paper03.html', { waitUntil: 'networkidle' });
  await p.waitForTimeout(1500);
  await p.pdf({
    path: __dirname + '/headroom-nowcast-2026-03.pdf',
    format: 'A4',
    printBackground: true,
    displayHeaderFooter: true,
    margin: { top: '19mm', bottom: '20mm', left: '18mm', right: '18mm' },
    headerTemplate: `<div style="width:100%;font-family:'IBM Plex Mono',monospace;font-size:6.6pt;
      letter-spacing:.14em;color:#8A979A;padding:0 18mm;display:flex;justify-content:space-between;">
      <span>WALKFORWARD RESEARCH &nbsp;·&nbsp; PAPER 2026/03</span>
      <span>DOI 10.5281/zenodo.22724955</span></div>`,
    footerTemplate: `<div style="width:100%;font-family:'IBM Plex Mono',monospace;font-size:6.6pt;
      letter-spacing:.14em;color:#8A979A;padding:0 18mm;display:flex;justify-content:space-between;">
      <span>v1.0 &nbsp;·&nbsp; 12 SEPTEMBER 2026 &nbsp;·&nbsp; CC BY 4.0</span>
      <span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>`,
  });
  await b.close();
  console.log('pdf written');
})();
