// Render an existing local report without model execution or external requests.
// node renderizar_informe_editorial.cjs HTML PDF RECEIPT --playwright MODULE [--browser EXE]
const fs = require('fs');
const path = require('path');
const { pathToFileURL } = require('url');

async function main() {
  const args = process.argv.slice(2);
  if (args.length < 5 || !args.includes('--playwright')) throw Error('Expected HTML PDF RECEIPT --playwright MODULE [--browser EXE]');
  const [input, output, receipt] = args.slice(0, 3).map(p => path.resolve(p));
  const modulePath = args[args.indexOf('--playwright') + 1];
  const browserIndex = args.indexOf('--browser');
  const { chromium } = require(path.resolve(modulePath));
  const browser = await chromium.launch({ headless: true, ...(browserIndex >= 0 ? {executablePath: args[browserIndex+1]} : {}) });
  const page = await browser.newPage();
  const errors = [], remote = [];
  page.on('pageerror', e => errors.push(e.message));
  await page.route('**/*', route => {
    const u = route.request().url();
    if (/^https?:/.test(u)) { remote.push(u); return route.abort(); }
    return route.continue();
  });
  await page.goto(pathToFileURL(input).href, { waitUntil: 'load' });
  await page.emulateMedia({media:'print'});
  await page.evaluate(() => document.fonts.ready);
  const layout = await page.evaluate(() => [...document.querySelectorAll('.content')].map((c,i) => {
    const r = c.getBoundingClientRect();
    let bottom = 0, left = 0, right = 0;
    for (const e of c.querySelectorAll('*')) {
      const b = e.getBoundingClientRect();
      if (b.height > 0) {
        bottom = Math.max(bottom,b.bottom-r.top);
        left = Math.min(left,b.left-r.left);
        right = Math.max(right,b.right-r.right);
      }
    }
    return {page:i+1, used:bottom, available:c.clientHeight, free:c.clientHeight-bottom,
      leftOverflow:left, rightOverflow:right, textChars:c.innerText.length,
      fontsLoaded:document.fonts.check('12px InterTT')};
  }));
  const result = {timestamp:new Date().toISOString(),input,output,pages:layout, errors,remoteRequests:remote};
  fs.writeFileSync(receipt,JSON.stringify(result,null,2)+'\n');
  if (layout.length !== 10 || layout.some(p => p.free < -1 || p.leftOverflow < -1 || p.rightOverflow > 1 || !p.fontsLoaded) || errors.length || remote.length) {
    await browser.close();
    throw Error('Report failed layout, font, page count or network checks; inspect receipt.');
  }
  await page.pdf({path:output, format:'A4', printBackground:true, preferCSSPageSize:true});
  await browser.close();
  console.log(JSON.stringify({status:'rendered',pages:layout.length,free:layout.map(x=>Math.round(x.free)),errors:errors.length,remoteRequests:remote.length}));
}
main().catch(e => {console.error(e.message);process.exitCode=1;});
