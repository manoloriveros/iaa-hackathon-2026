// Inspección funcional con DOM mínimo. No es captura o renderizado en navegador.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=fs.readFileSync(process.argv[2],'utf8');
function element(tag){return {tag,children:[],value:'',textContent:'',events:{},className:'',
  appendChild(child){this.children.push(child);if(this.tag==='select'&&this.children.length===1)this.value=child.value;return child;},
  replaceChildren(){this.children=[];if(this.tag==='select')this.value='';},
  createTHead(){return this.appendChild(element('thead'));},createTBody(){return this.appendChild(element('tbody'));},
  insertRow(){return this.appendChild(element('tr'));},insertCell(){return this.appendChild(element('td'));},
  addEventListener(name,fn){this.events[name]=fn;}};}
const nodes=Object.fromEntries(['case','reason','pair','periods','claims','search','group','groupcount'].map(id=>[id,element(['case','group'].includes(id)?'select':'div')]));
nodes.case.value='0';
const context=vm.createContext({document:{getElementById(id){assert.ok(nodes[id]);return nodes[id];},createElement:element}});
const scripts=[...source.matchAll(/<script>([\s\S]*?)<\/script>/g)];assert.equal(scripts.length,1);
vm.runInContext(scripts[0][1],context,{timeout:2000});
const examples=vm.runInContext('examples',context),proposal=vm.runInContext('proposal',context),histories=vm.runInContext('histories',context);
const checkRows=id=>nodes[id].children[0].children.find(x=>x.tag==='tbody').children;
const checks=[];function ok(name,fn){fn();checks.push({name,passed:true});}
ok('all_604_pair_options_load',()=>{assert.equal(proposal.length,604);assert.equal(nodes.group.children.length,604);assert.equal(nodes.groupcount.textContent,'604 de 604 parejas');});
for(let i=0;i<examples.length;i++)ok('case_'+examples[i].case_id+'_full_history',()=>{
  nodes.case.value=String(i);nodes.case.events.change();const e=examples[i],h=histories[e.line+'|'+e.policy_id];
  assert.equal(nodes.reason.textContent,e.reason);assert.equal(checkRows('claims').length,h.claims.length);assert.equal(checkRows('periods').length,h.periods.length);
  const renderedIds=checkRows('claims').map(row=>row.children[1].textContent);
  assert.deepEqual(renderedIds,Array.from(h.claims,r=>r.claim_id));
});
ok('eleven_examples_include_two_no_exclusion_controls',()=>{assert.equal(examples.length,11);for(const e of examples.filter(e=>e.duplicate_group===null)){
  nodes.case.value=String(examples.indexOf(e));nodes.case.events.change();assert.equal(checkRows('pair').length,0);assert.ok(checkRows('claims').every(row=>row.className!=='proposed-exclude'));
}});
ok('monetary_to_date_fields_render_as_numbers',()=>{const i=examples.findIndex(e=>e.case_id==='open_reserve');nodes.case.value=String(i);nodes.case.events.change();
  const fields=vm.runInContext('claimFields',context),e=examples[i],h=histories[e.line+'|'+e.policy_id];
  for(let r=0;r<h.claims.length;r++)for(const col of ['paid_to_date','incurred_to_date','recoveries','observed_net_CU']){
    const index=fields.indexOf(col);assert.equal(checkRows('claims')[r].children[index].textContent,String(h.claims[r][col]));
  }
});
ok('search_by_long_id_returns_its_single_pair',()=>{nodes.search.value='CL175619477';nodes.search.events.input();assert.equal(nodes.group.children.length,1);assert.equal(nodes.group.children[0].value,'DUP0001');nodes.group.events.change();assert.ok(checkRows('claims').some(row=>row.children[1].textContent==='CL40310602'));});
ok('two_pairs_in_one_policy_remain_two_events',()=>{nodes.search.value='M77733416';nodes.search.events.input();assert.equal(nodes.group.children.length,2);nodes.group.events.change();assert.equal(checkRows('pair').length,2);assert.equal(checkRows('claims').filter(row=>row.className==='proposed-exclude').length,2);});
ok('every_pair_opens_a_complete_policy_history',()=>{nodes.search.value='';nodes.search.events.input();for(const p of proposal){nodes.group.value=p.duplicate_group;nodes.group.events.change();const h=histories[p.line+'|'+p.policy_id];assert.equal(checkRows('claims').length,h.claims.length);assert.equal(checkRows('periods').length,h.periods.length);}});
ok('empty_search_does_not_invent_a_pair',()=>{nodes.search.value='NO_EXISTE_ABC123';nodes.search.events.input();assert.equal(nodes.group.children.length,0);assert.equal(nodes.groupcount.textContent,'0 de 604 parejas');});
ok('raw_csv_fallback_is_present',()=>{assert.ok(source.includes('<noscript>')&&source.includes('tables/frozen_pair_members.csv')&&source.includes('tables/proposed_pair_actions.csv'));});
process.stdout.write(JSON.stringify({passed:true,checks_count:checks.length,checks,real_browser_rendering:false,
  all_604_groups_exercised:true,scope:'Explorer and full policy/claim histories in a minimal DOM; no real browser rendering.'},null,2));
