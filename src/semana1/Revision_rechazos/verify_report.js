// DOM mínimo: verifica lógica y cada historial. No acredita renderizado de navegador.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=fs.readFileSync(process.argv[2],'utf8');
const match=source.match(/<script id="reviewData" type="application\/json">([\s\S]*?)<\/script>/);assert.ok(match);
const data=JSON.parse(match[1]);
const nodes=Object.fromEntries(['example','search','policy','matches','caseBody','reviewData'].map(id=>[id,{value:'',innerHTML:'',textContent:'',events:{},addEventListener(e,fn){this.events[e]=fn;}}]));
nodes.reviewData.textContent=match[1];
const context=vm.createContext({document:{getElementById(id){assert.ok(nodes[id]);return nodes[id];}},Intl});
const scripts=[...source.matchAll(/<script>([\s\S]*?)<\/script>/g)];assert.equal(scripts.length,1);vm.runInContext(scripts[0][1],context,{timeout:5000});
const checks=[];function ok(name,fn){fn();checks.push({check:name,passed:true});}
function verifyBody(pid){const h=data.histories[pid],body=nodes.caseBody.innerHTML;
 assert.ok(body.includes(pid));assert.equal((body.match(/<tr class=/g)||[]).length,h.policies.length+h.claims.length);
 for(const p of h.policies)assert.ok(body.includes(p.row_id)&&body.includes(p.period_start.slice(0,10))&&body.includes(p.period_end.slice(0,10)));
 for(const c of h.claims)assert.ok(body.includes(c.claim_id)&&body.includes(c.loss_date.slice(0,10))&&body.includes(c.report_date.slice(0,10)));
}
ok('2742 cohort options with complete index',()=>{assert.equal(data.index.length,2742);assert.equal((nodes.policy.innerHTML.match(/<option /g)||[]).length,2742);assert.equal(nodes.matches.textContent,'2742 de 2742 pólizas');});
for(const item of data.cases)ok('Explained real case '+item.policy_id,()=>{nodes.example.value=item.policy_id;nodes.example.events.change();verifyBody(item.policy_id);});
ok('Every frozen policy opens complete history',()=>{for(const r of data.index){nodes.policy.value=r.policy_id;nodes.policy.events.change();verifyBody(r.policy_id);}});
ok('Exact policy search and empty search behave correctly',()=>{nodes.search.value='B00134306';nodes.search.events.input();assert.equal(nodes.matches.textContent,'1 de 2742 pólizas');verifyBody('B00134306');nodes.search.value='NO_EXISTE_XXX';nodes.search.events.input();assert.equal(nodes.matches.textContent,'0 de 2742 pólizas');assert.ok(nodes.caseBody.innerHTML.includes('Sin coincidencias'));});
ok('Line search returns all motor policies',()=>{nodes.search.value='motor';nodes.search.events.input();assert.equal(nodes.matches.textContent,'1513 de 2742 pólizas');});
ok('Money is formatted as numbers and dates explicitly',()=>{for(const h of Object.values(data.histories))for(const claim of h.claims){for(const field of ['paid_to_date','incurred_to_date','recoveries','observed_net_CU'])assert.equal(vm.runInContext(`fmt(${JSON.stringify(field)},${JSON.stringify(claim[field])})`,context),new Intl.NumberFormat('es-CO',{maximumFractionDigits:4}).format(claim[field]));}});
ok('No invented 2025 claim observations',()=>{for(const h of Object.values(data.histories))assert.ok(h.claims.every(x=>x.loss_date<'2025'));});
ok('HTML escaping protects source content',()=>{assert.equal(vm.runInContext(`esc('<p>"&')`,context),'&lt;p&gt;&quot;&amp;');});
ok('CSV fallback and honest rendering scope retained',()=>{assert.ok(source.includes('<noscript>')&&source.includes('tables/cohort_and_control_source_histories.csv')&&source.includes('renderizado real'));});
const result={status:'passed_minimal_DOM_logic',passed:checks.length,failed:0,checks,all_2742_policies_exercised:true,real_browser_rendering:false};
if(process.argv[3]){assert.ok(!fs.existsSync(process.argv[3]));fs.writeFileSync(process.argv[3],JSON.stringify(result,null,2));}
process.stdout.write(JSON.stringify({status:result.status,passed:result.passed,all_2742_policies_exercised:true,real_browser_rendering:false}));
