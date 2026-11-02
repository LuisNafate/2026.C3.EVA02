"""Bound a command and terminate its complete process tree on timeout."""
import os,signal,subprocess

def call_bounded(args,timeout,**kwargs):
    if os.name=='nt':
        kwargs['creationflags']=subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        kwargs['start_new_session']=True
    process=subprocess.Popen(args,**kwargs)
    try:
        code=process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        if os.name=='nt':
            subprocess.run(['taskkill','/PID',str(process.pid),'/T','/F'],capture_output=True,timeout=10,check=False)
        else:
            os.killpg(process.pid,signal.SIGKILL)
        process.wait(timeout=10)
        raise
    if code:
        raise subprocess.CalledProcessError(code,args)
    return code
