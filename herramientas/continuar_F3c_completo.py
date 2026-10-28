"""Cola local finita de la unidad registrada; no es una automatización recurrente."""
from pathlib import Path
import argparse,json,os,subprocess,sys,time
from datetime import datetime,timezone
R=Path(__file__).resolve().parents[1]
OUT=R/'privado/semana2/mision017_fase2/F3c_validacion_completa_20261027'
def utc():return datetime.now(timezone.utc).isoformat()
def save(path,value):
    with path.open('x',encoding='utf8') as stream:json.dump(value,stream,indent=2)

def run(script,*args):
    print(json.dumps({'utc':utc(),'start':script,'args':args}),flush=True)
    tmp=OUT/'queue_live.tmp';tmp.write_text(json.dumps({'utc':utc(),'pid':os.getpid(),'status':'running','script':script,'args':args}),encoding='utf8');os.replace(tmp,OUT/'live_queue.json')
    token=datetime.now(timezone.utc).strftime('%H%M%S%f');logpath=OUT/('queue_child_'+token+'.log');lines=[]
    with logpath.open('x',encoding='utf8') as log:
        child=subprocess.Popen([sys.executable,str(R/'herramientas'/script),*args],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf8',env={**os.environ,'PYTHONIOENCODING':'utf-8'})
        for line in child.stdout:log.write(line);log.flush();print(line,end='',flush=True);lines.append(line)
        code=child.wait()
    if code:
        memory_guard=lines and lines[-1].strip()=='AssertionError: Insufficient memory before full fit; resume this stage later'
        assert memory_guard and script=='validar_F3c_completo.py',f'Child failed outside resumable resource guard: {logpath}'
        return False
    return True

def main():
    parser=argparse.ArgumentParser();g=parser.add_mutually_exclusive_group(required=True);g.add_argument('--previous-source-ended',action='store_true');g.add_argument('--wait-pid',type=int);args=parser.parse_args()
    save(OUT/('queue_resumed_'+datetime.now(timezone.utc).strftime('%H%M%S%f')+'.json'),{'utc':utc(),'pid':os.getpid(),'previous_source_ended_reconciled':args.previous_source_ended,'wait_pid':args.wait_pid,'new_submissions':0,'resource_resumes_max_per_line':4})
    if args.wait_pid:
        import ctypes
        kernel=ctypes.windll.kernel32;kernel.OpenProcess.restype=ctypes.c_void_p;kernel.WaitForSingleObject.argtypes=[ctypes.c_void_p,ctypes.c_ulong];kernel.CloseHandle.argtypes=[ctypes.c_void_p]
        handle=kernel.OpenProcess(0x100000,False,args.wait_pid);assert handle,'Own source PID not available; reconcile before running.'
        start=time.monotonic()
        try:
            while not (OUT/'motor_source_complete.json').exists():
                assert time.monotonic()-start<5400,'Finite wait expired.'
                assert kernel.WaitForSingleObject(handle,0)==258,'Motor ended without a complete receipt; reconcile its tool output before resuming.'
                time.sleep(10)
        finally:kernel.CloseHandle(handle)
    for line in ['motor','buildings','contents']:
        if (OUT/(line+'_source_complete.json')).exists():continue
        for attempt in range(5):
            if run('validar_F3c_completo.py','train','--line',line):break
            save(OUT/(line+'_resource_resume_'+str(attempt)+'.json'),{'utc':utc(),'reason':'Explicit pre-full-fit memory guard. Inner checkpoint preserved; no repeat of completed nativefits.','attempt':attempt})
            assert attempt<4,'Resource guards repeated; stop without altering recipe.'
            time.sleep(5)
        assert (OUT/(line+'_source_complete.json')).exists()
    if not (OUT/'parameters.json').exists():assert run('evaluar_F3c_completo.py','predict')
    assert (OUT/'target_controls.json').exists(),'Partial target run; manual reconciliation required.'
    if not (OUT/'results.json').exists():assert run('evaluar_F3c_completo.py','evaluate')
    if not (OUT/'verification.json').exists():assert run('verificar_F3c_completo.py','verify')
    if not (OUT/'closed.json').exists():assert run('cerrar_F3c_completo.py')
    print(json.dumps({'queue_complete':True,'new_submissions':0}),flush=True)

if __name__=='__main__':sys.stdout.reconfigure(encoding='utf8');main()
