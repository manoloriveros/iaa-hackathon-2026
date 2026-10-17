// Verifica la lógica del HTML en Node con un DOM mínimo; no simula una inspección de navegador.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '../../..');
const pointer = JSON.parse(fs.readFileSync(path.join(__dirname, 'current_run.json'), 'utf8'));
const out = path.join(root, pointer.workspace_relative_run);
const report = fs.readFileSync(path.join(out, 'informe.html'), 'utf8');
const script = report.match(/<script>([\s\S]*?)<\/script>/)[1];
const checks = [];
const nodes = {};
function node() {
  return { value: '', innerHTML: '', textContent: '', addEventListener() {}, appendChild() {},
    querySelectorAll() { return Array.from({length: (this.innerHTML.match(/<tr>/g)||[]).length-1}, node); }};
}
const document = {getElementById(id) {return nodes[id] ??= node();}, createElement:node};
const context = vm.createContext({document, Intl});
function check(name, fn) {fn();checks.push({check:name,passed:true});}
check('script_parses_and_renders_initial_queue',()=>{
  vm.runInContext(script,context);
  assert.equal(vm.runInContext('rows.length',context),3527);
  assert.match(nodes.count.textContent,/3527 filas; se muestran 50/);
});
check('lookup_returns_exact_policy',()=>{
  nodes.query.value='C00010235';vm.runInContext('update()',context);
  assert.equal(nodes.count.textContent,'1 filas; se muestran 1');
});
check('history_preserves_actual_peak_and_all_five_rows',()=>{
  vm.runInContext("show('C00010235','contents')",context);
  for(const id of ['C00510719','C01108116','C01709295','C02314938','C02924913']) assert.ok(nodes.history.innerHTML.includes(id));
  assert.ok(nodes.history.innerHTML.includes('37.700.000'));
});
check('route_filter_matches_108_no_reference_rows',()=>{
  nodes.query.value='';nodes.route.value='no_normal_same_policy_reference';
  vm.runInContext('update()',context);assert.equal(nodes.count.textContent,'108 filas; se muestran 50');
});
check('combined_line_and_route_filter_matches_46_contents_rows',()=>{
  nodes.line.value='contents';vm.runInContext('update()',context);
  assert.equal(nodes.count.textContent,'46 filas; se muestran 46');
});
check('dataset_values_are_html_escaped',()=>assert.equal(vm.runInContext("esc('<script>')",context),'&lt;script&gt;'));
const result={passed:true,checks_count:checks.length,checks,
  scope:'Offline JavaScript logic tested in Node with a minimal DOM; not live browser rendering or end-to-end browser verification.'};
fs.writeFileSync(path.join(out,'report_logic_verification.json'),JSON.stringify(result,null,2));
fs.copyFileSync(__filename,path.join(out,'source_snapshot',path.basename(__filename)));
process.stdout.write(JSON.stringify({passed:true,checks:checks.length})+'\n');
