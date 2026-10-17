// Prueba del explorador con DOM mínimo. No equivale a renderizado en navegador.
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const html = fs.readFileSync(process.argv[2], 'utf8');
function element(tag) {
  return {tag, children: [], textContent: '', value: '0', events: {},
    appendChild(child) { this.children.push(child); return child; },
    replaceChildren() { this.children = []; },
    createTHead() { return this.appendChild(element('thead')); },
    createTBody() { return this.appendChild(element('tbody')); },
    insertRow() { return this.appendChild(element('tr')); },
    insertCell() { return this.appendChild(element('td')); },
    addEventListener(name, fn) { this.events[name] = fn; }};
}
const nodes = Object.fromEntries(['case','reason','history'].map(id => [id, element(id)]));
const context = vm.createContext({document: {getElementById(id) { assert.ok(nodes[id]); return nodes[id]; }, createElement: element}});
const scripts = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]);
assert.equal(scripts.length, 1);
vm.runInContext(scripts[0], context, {timeout: 1000});
const cases = vm.runInContext('cases', context);
const fields = vm.runInContext('fields', context);
const checks = [{name:'single_self_contained_explorer_initializes', passed:true}];
assert.equal(cases.length, 6);
assert.equal(new Set(cases.map(c=>c.policy_id)).size, 6);
for (let i=0;i<cases.length;i++) {
  nodes.case.value = String(i);
  nodes.case.events.change();
  assert.equal(nodes.reason.textContent, cases[i].reason);
  assert.equal(nodes.history.children.length, 1);
  const table = nodes.history.children[0];
  const [thead, tbody] = table.children;
  assert.equal(thead.children[0].children.length, fields.length);
  assert.equal(tbody.children.length, cases[i].rows.length);
  for(let r=0;r<cases[i].rows.length;r++) {
    const cells = tbody.children[r].children;
    assert.equal(cells.length, fields.length);
    for(let col=0;col<fields.length;col++) {
      const field=fields[col]; let val=cases[i].rows[r][field];
      if(field.startsWith('period_')&&val) val=val.slice(0,10);
      assert.equal(cells[col].textContent, val===null?'Sin dato':String(val));
    }
  }
  checks.push({name:`case_${cases[i].policy_id}_all_rows_fields_and_switch`, passed:true});
}
assert.ok(html.includes('<noscript>') && html.includes('tables/case_histories.csv'));
checks.push({name:'csv_fallback_without_javascript', passed:true});
process.stdout.write(JSON.stringify({passed:true, checks_count:checks.length, checks,
  real_browser_rendering:false, scope:'Report explorer logic in a minimal DOM; all six cases and all displayed cells.'}, null, 2));
