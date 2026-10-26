/* Pruebas de interacción y presentación local. NODE_PATH debe incluir Playwright. */
const fs=require('fs'),path=require('path'),crypto=require('crypto'),{pathToFileURL}=require('url'),{chromium}=require('playwright');
const repo=path.resolve(__dirname,'..'),root=path.resolve(repo,'../..');
const data=JSON.parse(fs.readFileSync(path.join(repo,'docs/entrega/analisis/datos_panel.json'),'utf8'));
const run=path.join(root,data.private_run),out=path.join(run,'ui');fs.mkdirSync(out,{recursive:true});
(async()=>{
 const browser=await chromium.launch({headless:true,channel:process.env.PANEL_BROWSER_CHANNEL||'chrome',downloadsPath:path.join(out,'descargas')});
 const page=await browser.newPage({viewport:{width:1440,height:1000},acceptDownloads:true});
 const errors=[],network=[],checks=[];
 page.on('pageerror',e=>errors.push(String(e)));
 page.on('request',r=>{if(/^https?:/.test(r.url()))network.push(r.url())});
 function check(label,ok,detail){checks.push({control:label,pasa:!!ok,detalle:detail});if(!ok)throw Error(label)}
 await page.goto(pathToFileURL(path.join(repo,'docs/entrega/panel_analisis.html')).href);
 await page.waitForSelector('#kpis .value');
 check('Sin errores JS iniciales',errors.length===0,errors);
 await page.screenshot({path:path.join(out,'escritorio.png'),fullPage:false});
 let combinations=0;
 for(const market of ['all','developed','emerging'])for(const line of ['all','motor','buildings','contents'])for(const year of ['common','history','all','2021','2022','2023','2024','2025']){
   await page.selectOption('#market',market);await page.selectOption('#line',line);await page.selectOption('#year',year);
   const ys=year==='common'?[2023,2024]:year==='history'?[2021,2022,2023,2024]:year==='all'?[2021,2022,2023,2024,2025]:[+year];
   const rows=data.portfolio.filter(r=>(market==='all'||market===r.market)&&(line==='all'||line===r.line)&&ys.includes(r.year));
   const n=rows.reduce((s,r)=>s+r.rows,0),text=await page.locator('#kpis .value').first().textContent();
   check(`Filtros ${market}/${line}/${year}`,text===n.toLocaleString('es-CO'),text);
   const bad=await page.locator('main').innerText();check('Sin no finitos en '+market+'/'+line+'/'+year,!/\b(NaN|Infinity|undefined)\b/.test(bad));
   if(year==='2025')check('Test sin etiqueta '+market+'/'+line,(await page.locator('#kpis .value').nth(2).textContent())==='Sin etiqueta');
   combinations++;
 }
 await page.selectOption('#year','2025');
 const dl=page.waitForEvent('download');await page.click('#csv');const download=await dl;
 await download.saveAs(path.join(out,'test_agregado.csv'));
 const csv=fs.readFileSync(path.join(out,'test_agregado.csv'),'utf8').replace(/^\uFEFF/,'').trim().split(/\r?\n/);
 const keys=csv.shift().split(','),ix=keys.indexOf('T0_cents');
 check('CSV test mantiene costes vacíos',csv.length>0&&csv.every(r=>r.split(',')[ix]===''));
 await page.click('#reset');
 check('Restablecer filtros',await page.inputValue('#year')==='common'&&await page.inputValue('#line')==='all');
 for(const origin of ['all','policies','customers','addresses','weather']){
  await page.selectOption('#origin',origin);check('Filtro faltantes '+origin,(await page.locator('#missing-bars').innerText()).length>0);
 }
 await page.selectOption('#origin','all');
 await page.locator('#cartera summary').click();
 check('Tabla de cartera desplegada',await page.locator('#portfolio-table table').isVisible());
 await page.locator('#cartera summary').click();
 for(const width of [320,390,768,1440]){
   await page.setViewportSize({width,height:1000});
   check('Sin desborde de página '+width,await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),await page.evaluate(()=>({body:document.documentElement.scrollWidth,viewport:innerWidth})));
   await page.screenshot({path:path.join(out,`ancho_${width}.png`),fullPage:false});
 }
 await page.setViewportSize({width:1440,height:1000});
 await page.locator('#contraste').screenshot({path:path.join(out,'contraste.png')});
 await page.locator('#calidad').screenshot({path:path.join(out,'calidad.png')});
 await page.locator('#faltantes').screenshot({path:path.join(out,'faltantes.png')});
 await page.emulateMedia({media:'print'});
 check('Impresión oculta controles',!(await page.locator('.filters').isVisible()));
 await page.emulateMedia({media:'screen'});
 await page.keyboard.press('Control+Home');await page.keyboard.press('Tab');
 check('Navegación por teclado',await page.evaluate(()=>document.activeElement.tagName!=='BODY'));
 // El panel previo conserva cifras S41 y enlaza la ampliación en ambos idiomas.
 await page.goto(pathToFileURL(path.join(repo,'docs/entrega/panel_modelo.html')).href);
 await page.waitForSelector('a[href="panel_analisis.html"]');
 check('Panel previo enlaza ampliación',await page.locator('a[href="panel_analisis.html"]').first().isVisible());
 for(const lang of ['en','es']){
  await page.locator(`[data-idioma="${lang}"]`).click();
  check('Panel previo idioma '+lang,(await page.locator('#contenido').innerText()).includes('S41'));
 }
 await page.locator('[data-tema="dark"]').click();
 check('Tema oscuro previo conserva contenido',(await page.locator('#contenido').innerText()).includes('S41'));
 await page.locator('a[href="panel_analisis.html"]').first().click();
 await page.waitForSelector('#kpis .value');
 check('Navegación al análisis conjunto',page.url().endsWith('/panel_analisis.html'));
 // Los destinos de informe enlazados deben existir en el paquete local.
 const targets=await page.locator('a[href]').evaluateAll(nodes=>nodes.map(n=>n.getAttribute('href')).filter(h=>h&&!h.startsWith('#')));
 for(const href of targets)check('Destino local '+href,fs.existsSync(path.join(repo,'docs/entrega',href)));
 check('Sin red',network.length===0,network);check('Sin errores JS al finalizar',errors.length===0,errors);
 await browser.close();
 const receipt={autor:'Codex',utc:new Date().toISOString(),data_sha256:crypto.createHash('sha256').update(fs.readFileSync(path.join(repo,'docs/entrega/analisis/datos_panel.json'))).digest('hex'),passed:checks.length,failed:0,combinations,errors,network,checks};
 fs.writeFileSync(path.join(run,'validacion_ui.json'),JSON.stringify(receipt,null,1)+'\n');
 console.log(JSON.stringify({passed:checks.length,combinations,errors,network,out}));
})().catch(e=>{console.error(e);process.exit(1)});
