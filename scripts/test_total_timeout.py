import sys,time,tempfile,subprocess,ctypes
from pathlib import Path
from bounded_process import call_bounded
call_bounded([sys.executable,'-c','pass'],timeout=5)
try:
 call_bounded([sys.executable,'-c','raise SystemExit(3)'],timeout=5)
 raise AssertionError('Expected nonzero exit')
except subprocess.CalledProcessError as e:assert e.returncode==3
with tempfile.TemporaryDirectory(prefix='eva02_timeout_') as folder:
 pidfile=Path(folder)/'pid.txt'
 code="import subprocess,sys,time; from pathlib import Path; p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)']); Path(sys.argv[1]).write_text(str(p.pid)); time.sleep(30)"
 start=time.monotonic()
 try:
  call_bounded([sys.executable,'-c',code,str(pidfile)],timeout=2)
  raise AssertionError('Expected timeout')
 except subprocess.TimeoutExpired:pass
 assert time.monotonic()-start<15
 assert pidfile.exists(),'Child process was not created'
 handle=ctypes.windll.kernel32.OpenProcess(0x1000,False,int(pidfile.read_text()))
 if handle:
  exitcode=ctypes.c_ulong();assert ctypes.windll.kernel32.GetExitCodeProcess(handle,ctypes.byref(exitcode));ctypes.windll.kernel32.CloseHandle(handle)
  assert exitcode.value!=259,'Child survived timeout'
print('OK: normal exit, failure, timeout and full process-tree termination')
