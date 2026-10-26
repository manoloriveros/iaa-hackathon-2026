/* Verifica la comparación simultánea de ambas semanas, desde archivos locales. */
const fs=require('fs'),path=require('path'),crypto=require('crypto'),{pathToFileURL}=require('url'),{chromium}=require('playwright');
const repo=path.resolve(__dirname,'..'),root=path.resolve(repo,'../..'),ent=path.join(repo,'docs/entrega');
const data=JSON.parse(fs.readFileSync(path.join(ent,'analisis/datos_panel.json'),'utf8'));
const meta=JSON.parse(fs.readFileSync(path.join(ent,'informe_final/datos_informe.json'),'utf8'));
const run=path.join(root,meta.run),out=path.join(run,'ui');fs.mkdirSync(out,{recursive:true});
(async()=>{
 const browser=await chromium.launch({channel:'chrome',headless:true,downloadsPath:path.join(out,'descargas')});
 const page=await browser.newPage({viewport:{width:1440,height:1050},acceptDownloads:true}),checks=[],errors=[],network=[];
 const check=(name,ok,detail)=>{checks.push({control:name,pasa:!!ok,detalle:detail});if(!ok)throw Error(name)};
 page.on('pageerror',e=>errors.push(String(e)));page.on('request',r=>{if(/^https?:/.test(r.url()))network.push(r.url())});
 await page.goto(pathToFileURL(path.join(ent,'panel_analisis.html')).href);await page.waitForSelector('#summary-table table');
 await page.screenshot({path:path.join(out,'comparacion_escritorio.png'),fullPage:false});
 await page.locator('.two').first().screenshot({path:path.join(out,'comparacion_ramos.png')});
 const metricValue=(r,k)=>{
  const n=s=>r.reduce((a,x)=>a+(x[s]??0),0);if(k==='exposure')return n('exposure');if(r.every(x=>x.is_test))return null;
  return k==='rate'?n('T0_cents')/100/n('exposure'):k==='frequency'?100*n('accepted')/n('exposure'):k==='severity'?n('T0_cents')/100/n('positive'):k==='reserve'?100*n('reserve_cents')/n('T0_cents'):100*(n('rows')-n('positive_periods'))/n('rows');
 };
 let cases=0;
 for(const year of ['common','2023','2024','2025'])for(const line of ['all','motor','buildings','contents'])for(const metric of ['rate','frequency','severity','reserve','zero','exposure']){
  await page.selectOption('#year',year);await page.selectOption('#line',line);await page.selectOption('#metric',metric);
  const years=year==='common'?[2023,2024]:[+year];const lines=line==='all'?['motor','buildings','contents']:[line];
  check(`Ambas semanas visibles ${year}/${line}/${metric}`,(await page.locator('#summary-table thead').innerText()).includes('Desarrollado')&&(await page.locator('#summary-table thead').innerText()).includes('Emergente'));
  for(const l of lines)for(const [m,week] of [['developed','S1'],['emerging','S2']]){
   const rows=data.portfolio.filter(r=>r.market===m&&r.line===l&&years.includes(r.year)),expected=metricValue(rows,metric);
   const value=await page.locator(`.pair[data-line="${l}"] [data-week="${week}"]`).getAttribute('data-value');
   check(`Valor ${year}/${l}/${metric}/${week}`,expected===null?value==='':Math.abs(Number(value)-expected)<1e-8);
  }
  check(`Sin valores inválidos ${year}/${line}/${metric}`,!(/\b(NaN|Infinity|undefined)\b/.test(await page.locator('main').innerText())));cases++;
 }
 // El CSV corresponde a la comparación mostrada y conserva nulos de test.
 await page.selectOption('#year','2025');await page.selectOption('#line','all');await page.selectOption('#metric','rate');
 let promise=page.waitForEvent('download');await page.click('#csv');let download=await promise;await download.saveAs(path.join(out,'comparacion_test.csv'));
 let csv=fs.readFileSync(path.join(out,'comparacion_test.csv'),'utf8').replace(/^\uFEFF/,'').trim().split(/\r?\n/);csv.shift();
 check('Exportación test sin costes inventados',csv.length===3&&csv.every(s=>{let x=s.split(',');return x[4]===''&&x[5]===''}));
 await page.selectOption('#metric','exposure');promise=page.waitForEvent('download');await page.click('#csv');download=await promise;await download.saveAs(path.join(out,'comparacion_exposicion.csv'));
 csv=fs.readFileSync(path.join(out,'comparacion_exposicion.csv'),'utf8').replace(/^\uFEFF/,'').trim().split(/\r?\n/);csv.shift();
 check('Exposición de test exportada',csv.every(s=>{let x=s.split(',');return Number(x[4])>0&&Number(x[5])>0}));
 await page.click('#reset');check('Restablecer filtros',await page.inputValue('#year')==='common'&&await page.inputValue('#metric')==='rate');
 for(const origin of ['all','policies','customers','addresses','weather']){
  await page.selectOption('#origin',origin);check('Tabla de nulos '+origin,(await page.locator('#missing-table table').innerText()).includes('S1'));
 }
 await page.selectOption('#origin','all');
 await page.locator('#quality details summary').click();check('Esquema desplegable',await page.locator('#schema-table table').isVisible());await page.locator('#quality details summary').click();
 for(const width of [320,390,768,1440]){
  await page.setViewportSize({width,height:1050});await page.evaluate(()=>scrollTo(0,0));
  check('Sin desborde horizontal '+width,await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  await page.screenshot({path:path.join(out,`ancho_${width}.png`),fullPage:false});
 }
 await page.setViewportSize({width:1440,height:1050});
 for(const section of ['comparison-main','composition','quality','report'])await page.locator('#'+section).screenshot({path:path.join(out,section+'.png')});
 check('Tres figuras cargadas',await page.locator('.thumbs img').evaluateAll(imgs=>imgs.length===3&&imgs.every(i=>i.complete&&i.naturalWidth>0)));
 const links=await page.locator('a[href]').evaluateAll(a=>a.map(x=>x.getAttribute('href')).filter(x=>x&&!x.startsWith('#')&&!x.startsWith('data:')));
 for(const href of links)check('Enlace local '+href,fs.existsSync(path.resolve(ent,href)));
 await page.emulateMedia({media:'print'});check('Impresión sin controles',!await page.locator('.filters').isVisible());await page.emulateMedia({media:'screen'});
 await page.keyboard.press('Control+Home');await page.keyboard.press('Tab');check('Navegación de teclado',await page.evaluate(()=>document.activeElement.tagName!=='BODY'));
 await page.goto(pathToFileURL(path.join(ent,'panel_modelo.html')).href+'#limites');await page.waitForSelector('a[href="panel_analisis.html"]');await page.locator('a[href="panel_analisis.html"]').first().click();await page.waitForSelector('#summary-table table');
 check('Acceso desde el panel anterior',page.url().endsWith('/panel_analisis.html'));
 check('Cero errores JS',errors.length===0,errors);check('Cero solicitudes de red',network.length===0,network);
 const receipt={utc:new Date().toISOString(),autor:'Codex',checks,passed:checks.length,failed:0,combinations:cases,errors,network,html_sha256:crypto.createHash('sha256').update(fs.readFileSync(path.join(ent,'panel_analisis.html'))).digest('hex')};
 fs.writeFileSync(path.join(run,'verificacion_ui.json'),JSON.stringify(receipt,null,1)+'\n');await browser.close();
 console.log(JSON.stringify({passed:receipt.passed,combinations:cases,errors,network,out}));
})().catch(e=>{console.error(e);process.exit(1)});
