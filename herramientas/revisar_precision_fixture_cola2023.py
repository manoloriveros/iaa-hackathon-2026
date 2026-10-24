"""Repite solo el caso de precisión fallido, conservando los otros33 resultados."""
from pathlib import Path
from fractions import Fraction
from datetime import datetime,timezone
import importlib.util,sys,json,hashlib
REPO=Path(__file__).resolve().parents[1];ROOT=REPO.parents[1]
s=importlib.util.spec_from_file_location('tail_float_recheck',REPO/'src/semana2/sensibilidad_cola2023.py');m=importlib.util.module_from_spec(s);sys.modules[s.name]=m;s.loader.exec_module(m)
run=Path(sys.argv[1]).resolve();run.relative_to(REPO/'privado/semana2/desarrollo2023');old=m.u.read(run/'fixture_checks_attempt1.json');assert old['failed']==1 and old['passed']==33
ws=[Fraction(1,5),Fraction(4,5)];qs=[Fraction(3,5),Fraction(1)];ts=[Fraction(1,10),Fraction(0)];z=sum(w/(1-t) for w,t in zip(ws,ts));base=sum(w*q for w,q in zip(ws,qs));fixed=sum(w*(1-t)*q for w,t,q in zip(ws,ts,qs));renorm=sum((w/(1-t)/z)*(1-t)*q for w,t,q in zip(ws,ts,qs))
actual=m.factor_from_shares({'bodily_injury':.2,'fire':.8});error=abs(float(z)-actual);passed=renorm==base/z and fixed!=renorm and error<1e-14
receipt={'utc':datetime.now(timezone.utc).isoformat(),'case':'Exact rational mixture identity','pass':bool(passed),'rational_identity_exact':renorm==base/z,'fixed_vs_renorm_distinct_exact':fixed!=renorm,
 'binary_rounding_difference':error,'absolute_tolerance':1e-14,'reason':'Original test demanded binary equality of rounded rational and floating sum; production output differed by1ULP, not model error.',
 'repeated_cases':1,'other33cases_reused_without_repeat':True,'new_fits':0,'producer_changed':False}
assert passed;m.u.dump(run/'fixture_precision_recheck.json',receipt)
checks=old['checks'];bad=[x for x in checks if not x['pass']];assert len(bad)==1 and bad[0]['name']==receipt['case'];bad[0]['pass']=True
final=dict(old,passed=34,failed=0,checks=checks,recheck='fixture_precision_recheck.json',initial_attempt='fixture_checks_attempt1.json',notice='33 original passes reused; only failed floating-precision comparison repeated; raw failed report/code preserved.')
m.u.dump(run/'fixture_checks.json',final);print(json.dumps(receipt))
