"""Cola local finita de la unidad registrada; no es una automatización recurrente."""
from pathlib import Path
import importlib.util,json,os,subprocess,sys,time
R=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('F3c_queue',R/'herramientas/validar_F3c_completo.py');f=importlib.util.module_from_spec(s);s.loader.exec_module(f)

def run(script,*args):
    print(json.dumps({'utc':f.utc(),'start':script,'args':args}),flush=True)
    f.live('queue',{'pid':os.getpid(),'status':'running','script':script,'args':args})
    subprocess.run([sys.executable,str(R/'herramientas'/script),*args],check=True,env={**os.environ,'PYTHONIOENCODING':'utf-8'})

def main():
    f.guard();start=time.monotonic();f.dump(f.OUT/'queue_started.json',{'utc':f.utc(),'pid':os.getpid(),'source_waiting_pid':50536,'maximum_wait_seconds':5400,'new_submissions':0})
    while not (f.OUT/'motor_source_complete.json').exists():
        assert time.monotonic()-start<5400,'Finite wait expired; reconcile motor rather than relaunch.'
        assert f.psutil.pid_exists(50536),'Motor ended without completion receipt; reconcile its failure before continuing.'
        time.sleep(10)
    for line in ['buildings','contents']:
        if not (f.OUT/(line+'_source_complete.json')).exists():run('validar_F3c_completo.py','train','--line',line)
    if not (f.OUT/'parameters.json').exists():run('evaluar_F3c_completo.py','predict')
    assert (f.OUT/'target_controls.json').exists(),'Partial target run; manual reconciliation required.'
    if not (f.OUT/'results.json').exists():run('evaluar_F3c_completo.py','evaluate')
    if not (f.OUT/'verification.json').exists():run('verificar_F3c_completo.py','verify')
    if not (f.OUT/'closed.json').exists():run('cerrar_F3c_completo.py')
    f.live('queue',{'pid':os.getpid(),'status':'completed','new_submissions':0});print(json.dumps({'queue_complete':True,'new_submissions':0}),flush=True)

if __name__=='__main__':sys.stdout.reconfigure(encoding='utf8');main()
