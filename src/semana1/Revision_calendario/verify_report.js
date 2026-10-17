// Verifica lógica interactiva en un DOM mínimo; no acredita renderizado de navegador.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=fs.readFileSync(process.argv[2],'utf8');
const payload=source.match(/<script id="caseData" type="application\/json">([\s\S]*?)<\/script>/);
assert.ok(payload);const cases=JSON.parse(payload[1]);
const nodes=Object.fromEntries(['caseSelect','caseBody','previousCase','nextCase','caseData'].map(id=>[id,{value:'0',innerHTML:'',textContent:'',events:{},addEventListener(e,fn){this.events[e]=fn;}}]));
nodes.caseData.textContent=payload[1];
const context=vm.createContext({document:{getElementById(id){assert.ok(nodes[id]);return nodes[id];}},Intl});
const scripts=[...source.matchAll(/<script>([\s\S]*?)<\/script>/g)];assert.equal(scripts.length,1);
vm.runInContext(scripts[0][1],context,{timeout:2000});
const checks=[];function ok(name,fn){fn();checks.push({check:name,passed:true});}
ok('Thirteen options equal thirteen complete cases',()=>{assert.equal(cases.length,13);assert.equal([...source.matchAll(/<option value=/g)].length,13);});
for(let i=0;i<cases.length;i++)ok('Complete tables render for '+cases[i].case.policy_id,()=>{
 nodes.caseSelect.value=String(i);nodes.caseSelect.events.change();const item=cases[i],body=nodes.caseBody.innerHTML;
 assert.ok(body.includes(item.case.policy_id));
 assert.equal((body.match(/<tbody>/g)||[]).length,1+(item.claims.length>0?1:0));
 assert.equal((body.match(/<tr class=/g)||[]).length,item.policies.length+item.claims.length);
 for(const p of item.policies)assert.ok(body.includes(p.row_id));
 for(const c of item.claims)assert.ok(body.includes(c.claim_id)&&body.includes(c.loss_date.slice(0,10))&&body.includes(c.report_date.slice(0,10)));
});
ok('Money fields are numeric, not mistaken for dates',()=>{
 for(const item of cases)for(const claim of item.claims)for(const field of ['paid_to_date','incurred_to_date','recoveries','observed_net_CU']){
  const value=vm.runInContext(`format(${JSON.stringify(field)},${JSON.stringify(claim[field])})`,context);
  assert.equal(value,new Intl.NumberFormat('es-CO',{maximumFractionDigits:4}).format(claim[field]));
 }
});
ok('Navigation wraps in both directions',()=>{nodes.caseSelect.value='12';nodes.nextCase.events.click();assert.equal(nodes.caseSelect.value,'0');nodes.previousCase.events.click();assert.equal(nodes.caseSelect.value,'12');});
ok('Escaping protects data content',()=>{assert.equal(vm.runInContext(`esc('<x>"&')`,context),'&lt;x&gt;&quot;&amp;');});
ok('No cases invent 2025 claim records',()=>{for(const item of cases)assert.ok(item.claims.every(x=>x.loss_date<'2025'));});
const result={status:'passed_minimal_DOM_logic',passed:checks.length,failed:0,checks,real_browser_rendering:false};
if(process.argv[3]){assert.ok(!fs.existsSync(process.argv[3]));fs.writeFileSync(process.argv[3],JSON.stringify(result,null,2));}
process.stdout.write(JSON.stringify({status:result.status,passed:result.passed,real_browser_rendering:false}));
