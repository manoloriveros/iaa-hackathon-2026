// Prueba de lógica sobre DOM mínimo; no acredita renderizado real del navegador.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=fs.readFileSync(process.argv[2],'utf8'),match=source.match(/<script id="reviewData" type="application\/json">([\s\S]*?)<\/script>/);
assert.ok(match);const data=JSON.parse(match[1]);
const nodes=Object.fromEntries(['reviewData','example','search','pending','matches','caseBody'].map(id=>[id,{value:'',innerHTML:'',textContent:'',events:{},addEventListener(e,fn){this.events[e]=fn;}}]));
nodes.reviewData.textContent=match[1];const context=vm.createContext({document:{getElementById(id){assert.ok(nodes[id]);return nodes[id];}},Intl});
const scripts=[...source.matchAll(/<script>([\s\S]*?)<\/script>/g)];assert.equal(scripts.length,1);vm.runInContext(scripts[0][1],context,{timeout:5000});
const checks=[];function ok(name,fn){fn();checks.push({check:name,passed:true});}
function bodyMatches(rid){const row=data.index.find(x=>x.row_id===rid),h=data.histories[row.policy_id],body=nodes.caseBody.innerHTML;
 assert.ok(body.includes(rid)&&body.includes(row.policy_id));
 for(const p of h.policies){assert.ok(body.includes(p.row_id));assert.ok(body.includes(p.period_start.slice(0,10)));}
 for(const cl of h.claims){assert.ok(body.includes(cl.claim_id));assert.ok(body.includes(cl.loss_date.slice(0,10)));}
 for(const ref of data.references.filter(x=>x.pending_row_id===rid))assert.ok(body.includes(ref.row_id));
 const refs=data.references.filter(x=>x.pending_row_id===rid).length;
 assert.equal((body.match(/<tr class=/g)||[]).length,h.policies.length+h.claims.length+h.addresses.length+refs);
 // Source claims/references may repeat the selected row ID; only one policy-period focus row is required.
 assert.equal((body.match(/class="focus"/g)||[]).length,1);
}
ok('All 1454 options load',()=>{assert.equal(data.index.length,1454);assert.equal((nodes.pending.innerHTML.match(/<option /g)||[]).length,1454);assert.equal(nodes.matches.textContent,'1454 de 1454 periodos pendientes');});
for(const e of data.cases)ok('Explained case '+e.policy_id,()=>{nodes.example.value=e.focus_row_id;nodes.example.events.change();bodyMatches(e.focus_row_id);assert.ok(nodes.caseBody.innerHTML.includes(e.interpretation));});
ok('All 1454 rows open every source policy, claim and reference',()=>{for(const row of data.index){nodes.pending.value=row.row_id;nodes.pending.events.change();bodyMatches(row.row_id);}});
ok('Search policy with two pending rows and empty result',()=>{const count=data.index.filter(r=>r.policy_id==='B19256617').length;assert.equal(count,2);nodes.search.value='B19256617';nodes.search.events.input();assert.equal(nodes.matches.textContent,'2 de 1454 periodos pendientes');nodes.search.value='NO_EXISTE_123';nodes.search.events.input();assert.equal(nodes.matches.textContent,'0 de 1454 periodos pendientes');assert.ok(nodes.caseBody.innerHTML.includes('Sin coincidencias'));});
ok('Group search and scenario annotation',()=>{nodes.search.value='A_retrospective_D34';nodes.search.events.input();assert.equal(nodes.matches.textContent,'879 de 1454 periodos pendientes');assert.equal(data.index.filter(r=>r.retrospective_scenario_candidate_NOT_APPLIED).length,867);});
ok('Monetary values and date strings use appropriate formatting',()=>{assert.equal(vm.runInContext("fmt('sum_insured',237000000)",context),new Intl.NumberFormat('es-CO',{maximumFractionDigits:4}).format(237000000));assert.equal(vm.runInContext("fmt('period_start','2023-01-01T00:00:00.000')",context),'2023-01-01');});
ok('Escaping and CSV fallback remain available',()=>{assert.equal(vm.runInContext(`esc('<x>"&')`,context),'&lt;x&gt;&quot;&amp;');assert.ok(source.includes('<noscript>')&&source.includes('tables/pending_assessment.csv'));});
const result={status:'passed_minimal_DOM_logic',passed:checks.length,failed:0,checks,all_1454_rows_exercised:true,real_browser_rendering:false};
if(process.argv[3]){assert.ok(!fs.existsSync(process.argv[3]));fs.writeFileSync(process.argv[3],JSON.stringify(result,null,2));}
process.stdout.write(JSON.stringify({status:result.status,passed:result.passed,all_1454_rows_exercised:true}));
