// Comprueba búsqueda/filtros con DOM mínimo, sin afirmar renderizado de navegador.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const html=fs.readFileSync(process.argv[2],'utf8');
const controlMatches=[...html.matchAll(/<tr class="control" id="([^"]+)" data-priority="([^"]+)" data-status="([^"]+)">([\s\S]*?)<\/tr>/g)];
const controls=controlMatches.map(m=>({id:m[1],dataset:{priority:m[2],status:m[3]},textContent:m[4].replace(/<[^>]+>/g,' '),hidden:false}));
const fields=[...html.matchAll(/<tr class="field">([\s\S]*?)<\/tr>/g)].map(m=>({textContent:m[1].replace(/<[^>]+>/g,' '),hidden:false}));
const nodes=Object.fromEntries(['search','priority','status','count','fieldsearch'].map(id=>[id,{value:'',textContent:'',events:{},addEventListener(name,fn){this.events[name]=fn;}}]));
const context=vm.createContext({document:{getElementById(id){assert.ok(nodes[id]);return nodes[id];},querySelectorAll(selector){if(selector==='#controls tbody tr')return controls;if(selector==='#fields tbody tr')return fields;throw Error(selector);}}});
const scripts=[...html.matchAll(/<script>([\s\S]*?)<\/script>/g)];assert.equal(scripts.length,1);
vm.runInContext(scripts[0][1],context,{timeout:1000});
const checks=[];function ok(name,fn){fn();checks.push({name,passed:true});}
ok('58_controls_visible_at_initialization',()=>{assert.equal(controls.length,58);assert.equal(controls.filter(r=>!r.hidden).length,58);assert.equal(nodes.count.textContent,'58 de 58 controles');});
ok('priority_P0_returns_28_controls',()=>{nodes.priority.value='P0';nodes.priority.events.input();assert.equal(controls.filter(r=>!r.hidden).length,28);});
ok('new_findings_filter_returns_seven_controls',()=>{nodes.priority.value='';nodes.status.value='hallazgo_nuevo';nodes.status.events.input();assert.equal(controls.filter(r=>!r.hidden).length,7);});
ok('NCB_search_finds_exact_review_VD33',()=>{nodes.status.value='';nodes.search.value='NCB';nodes.search.events.input();assert.deepEqual(controls.filter(r=>!r.hidden).map(r=>r.id),['VD33']);});
ok('unknown_search_does_not_invent_results',()=>{nodes.search.value='SIN_COINCIDENCIAS_ABC123';nodes.search.events.input();assert.equal(controls.filter(r=>!r.hidden).length,0);});
ok('reset_restores_all_controls',()=>{nodes.search.value='';nodes.search.events.input();assert.equal(controls.filter(r=>!r.hidden).length,58);});
ok('field_inventory_has_105_searchable_rows',()=>{assert.equal(fields.length,105);nodes.fieldsearch.value='SIN_COINCIDENCIAS_ABC123';nodes.fieldsearch.events.input();assert.equal(fields.filter(r=>!r.hidden).length,0);nodes.fieldsearch.value='';nodes.fieldsearch.events.input();assert.equal(fields.filter(r=>!r.hidden).length,105);});
process.stdout.write(JSON.stringify({passed:true,checks_count:checks.length,checks,real_browser_rendering:false},null,2));
