const fs=require('fs'),path=require('path'),crypto=require('crypto'),{pathToFileURL}=require('url'),{chromium}=require('playwright');
const repo=path.resolve(__dirname,'..'),root=path.resolve(repo,'../..'),ent=path.join(repo,'docs/entrega');
const v=JSON.parse(fs.readFileSync(path.join(ent,'analisis/validaciones_panel.json'),'utf8'));
const d=JSON.parse(fs.readFileSync(path.join(ent,'analisis/datos_panel.json'),'utf8')),run=path.join(root,v.run),out=path.join(run,'ui');fs.mkdirSync(out,{recursive:true});
(async()=>{
 const browser=await chromium.launch({channel:'chrome',headless:true,downloadsPath:path.join(out,'descargas')}),page=await browser.newPage({viewport:{width:1440,height:1050},acceptDownloads:true});
 const checks=[],errors=[],network=[];page.on('pageerror',e=>errors.push(String(e)));page.on('request',r=>{if(/^https?:/.test(r.url()))network.push(r.url())});
 function check(k,ok){checks.push({control:k,pasa:!!ok});if(!ok)throw Error(k)}
 await page.goto(pathToFileURL(path.join(ent,'panel_analisis.html')).href);await page.waitForSelector('#data-cards article');
 check('Seis controles de datos',await page.locator('#data-cards article').count()===6);
 check('Sin enlaces a documentos',await page.locator('a[href]').evaluateAll(xs=>xs.every(x=>x.getAttribute('href').startsWith('#'))));
 check('Sin galería ni documento incrustado',await page.locator('img,iframe,embed,object').count()===0);
 check('Todos los textos visibles son breves',await page.locator('p:visible').evaluateAll(xs=>xs.every(x=>x.textContent.trim().split(/\s+/).length<=40)));
 check('Sin errores al abrir',errors.length===0);
 await page.screenshot({path:path.join(out,'inicio.png'),fullPage:false});
 for(const year of ['V23','V24']){
  await page.selectOption('#local-year',year);const s=await page.locator('#local-table').innerText();
  for(const line of ['agregado','motor','buildings','contents'])check('D² guardado '+year+'/'+line,s.includes(v.week1.local[year][line].toLocaleString('es-CO',{minimumFractionDigits:5,maximumFractionDigits:5})));
 }
 for(const line of ['motor','buildings','contents']){
  await page.selectOption('#calibration-line',line);check('Curvas de calibración '+line,await page.locator('#calibration-chart path').count()===2);
  check('Diez grupos '+line,await page.locator('#calibration-table tbody tr').count()===10);
 }
 for(const id of ['P17','P30']){
  await page.selectOption('#experiment',id);const source=v.week2.experiments.find(x=>x.id===id);
  const rows=await page.locator('#gates-table tbody tr').allInnerTexts();check('Siete guardas '+id,rows.length===Object.keys(source.gates).length);
  check('Fallas conservadas '+id,rows.filter(x=>x.includes('No se cumple')).length===Object.values(source.gates).filter(x=>!x).length);
  check('Cinco escenarios '+id,await page.locator('#stress-table tbody tr').count()===5);
 }
 check('Intervalos sin prometer mejora',await page.locator('#ci-table tbody tr').count()===4&&(await page.locator('#robustness').innerText()).includes('Sin mejora concluyente'));
 check('Cohorte adversa visible',(await page.locator('#cohort-table-model').innerText()).includes('Pérdida en este contraste'));
 check('Reproducción actualizada',(await page.locator('#replication').innerText()).includes('Se recuperó f3_eval'));
 await page.locator('#data-cards details summary').first().click();check('Detalle de control accesible',await page.locator('#data-cards table').first().isVisible());await page.locator('#data-cards details summary').first().click();
 for(const id of ['models','robustness','replication'])await page.locator('#'+id).screenshot({path:path.join(out,id+'.png')});
 // Conserva las 96 comprobaciones de la comparación de datos, ahora en su desplegable.
 await page.locator('#data-explorer>summary').click();
 let cases=0;
 const expected=(rows,metric)=>{const sum=k=>rows.reduce((a,r)=>a+(r[k]??0),0);if(metric==='exposure')return sum('exposure');if(rows.every(r=>r.is_test))return null;return metric==='rate'?sum('T0_cents')/100/sum('exposure'):metric==='frequency'?100*sum('accepted')/sum('exposure'):metric==='severity'?sum('T0_cents')/100/sum('positive'):metric==='reserve'?100*sum('reserve_cents')/sum('T0_cents'):100*(sum('rows')-sum('positive_periods'))/sum('rows')};
 for(const year of ['common','2023','2024','2025'])for(const line of ['all','motor','buildings','contents'])for(const metric of ['rate','frequency','severity','reserve','zero','exposure']){
  await page.selectOption('#year',year);await page.selectOption('#line',line);await page.selectOption('#metric',metric);
  const years=year==='common'?[2023,2024]:[+year],lines=line==='all'?['motor','buildings','contents']:[line];
  for(const l of lines)for(const [m,week] of [['developed','S1'],['emerging','S2']]){
   const rows=d.portfolio.filter(r=>r.market===m&&r.line===l&&years.includes(r.year)),want=expected(rows,metric),actual=await page.locator(`.pair[data-line="${l}"] [data-week="${week}"]`).getAttribute('data-value');
   check('Explorador '+year+'/'+l+'/'+metric+'/'+week,want===null?actual==='':Math.abs(Number(actual)-want)<1e-8);
  }
  check('Sin no finitos '+year+'/'+line+'/'+metric,!/\b(NaN|Infinity|undefined)\b/.test(await page.locator('main').innerText()));cases++;
 }
 await page.selectOption('#year','2025');await page.selectOption('#line','all');await page.selectOption('#metric','rate');
 const downloadPromise=page.waitForEvent('download');await page.click('#csv');const download=await downloadPromise;await download.saveAs(path.join(out,'test.csv'));
 const csv=fs.readFileSync(path.join(out,'test.csv'),'utf8').replace(/^\uFEFF/,'').trim().split(/\r?\n/);csv.shift();check('Test exportado sin inventar costes',csv.length===3&&csv.every(row=>{const x=row.split(',');return x[4]===''&&x[5]===''}));
 await page.click('#reset');await page.locator('#data-explorer>summary').click();
 for(const width of [320,390,768,1440]){
  await page.setViewportSize({width,height:1050});await page.evaluate(()=>scrollTo(0,0));check('Sin desborde '+width,await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  await page.screenshot({path:path.join(out,`ancho_${width}.png`),fullPage:false});
 }
 await page.emulateMedia({media:'print'});check('Impresión sin controles',!await page.locator('.filters').isVisible());await page.emulateMedia({media:'screen'});
 check('Cero errores JavaScript',errors.length===0);check('Cero solicitudes HTTP',network.length===0);
 const receipt={utc:new Date().toISOString(),author:'Codex',passed:checks.length,failed:0,data_cases:cases,errors,network,checks,html_sha256:crypto.createHash('sha256').update(fs.readFileSync(path.join(ent,'panel_analisis.html'))).digest('hex')};
 fs.writeFileSync(path.join(run,'verificacion_ui.json'),JSON.stringify(receipt,null,1)+'\n');await browser.close();console.log(JSON.stringify({passed:receipt.passed,data_cases:cases,errors,network,out}));
})().catch(e=>{console.error(e);process.exit(1)});
