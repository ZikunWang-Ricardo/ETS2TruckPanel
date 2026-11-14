"""Real loopback TCP tests. Run outside restricted network sandbox if required."""
import json
import os
import socket
import struct
import threading
import time
import unittest

from touchtruck.bridge import run
from touchtruck.input import InputController


@unittest.skipUnless(os.environ.get('TOUCHTRUCK_TCP_TESTS') == '1', 'Enable loopback integration explicitly')
class RuntimeTests(unittest.TestCase):
    def test_pair_publish_hold_telemetry_loss_reconnect_close(self):
        class Memory:
            present = True
            def read(self):
                if not self.present: return None
                b=bytearray(32768); b[0]=1
                struct.pack_into('<Q',b,8,time.monotonic_ns())
                struct.pack_into('<I',b,40,12); struct.pack_into('<I',b,52,1)
                struct.pack_into('<f',b,1000,321)
                return b
            def close(self): pass
        memory=Memory(); events=[]; stop=threading.Event()
        inputs=InputController(lambda k,d:events.append((k,d)),lambda:True)
        listener=socket.socket();listener.bind(('127.0.0.1',0));listener.listen();listener.settimeout(3)
        errors=[]
        def worker():
            try: run('127.0.0.1',listener.getsockname()[1],input_controller=inputs,memory_reader=memory,stop_event=stop,reconnect_delay=.01)
            except Exception as exc: errors.append(exc)
        thread=threading.Thread(target=worker,daemon=True);thread.start()
        def receive_line(stream): return json.loads(stream.readline())
        def until(predicate):
            deadline=time.monotonic()+3
            while not predicate() and time.monotonic()<deadline: time.sleep(.02)
            self.assertTrue(predicate())
        try:
            conn,_=listener.accept();conn.settimeout(3)
            with conn:
                f=conn.makefile('rb')
                self.assertEqual(receive_line(f),{'type':'pair','id':'touchtruck'})
                conn.sendall(b'{"type":"in');conn.sendall(b'fo"}\n')
                values={}
                while 'touchtruck.fuel' not in values:
                    m=receive_line(f); values[m['id']]=m['value']
                self.assertEqual(values['touchtruck.fuel'],'321')
                conn.sendall(b'{"type":"down","actionId":"touchtruck.action.horn"}\n')
                until(lambda:(35,True) in events)
                memory.present=False
                until(lambda:(35,False) in events)
                self.assertFalse(inputs.held)
                while values.get('touchtruck.fuel')!='—':
                    m=receive_line(f);values[m['id']]=m['value']
                f.close()
            conn2,_=listener.accept();conn2.settimeout(3)
            with conn2:
                f=conn2.makefile('rb');self.assertEqual(receive_line(f)['type'],'pair')
                conn2.sendall(b'{"type":"info"}\n{"type":"closePlugin"}\n');f.close()
            thread.join(3)
            self.assertFalse(thread.is_alive())
            self.assertFalse(errors)
        finally:
            stop.set();listener.close();thread.join(3)


if __name__=='__main__': unittest.main()
