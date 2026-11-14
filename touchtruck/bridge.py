"""Touch Portal newline JSON client; no third-party runtime dependencies."""
import argparse
import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import select
import socket
import time

from .telemetry import SharedMemory, SnapshotTracker, decode_snapshot, disconnected, FLAGS
from .input import WindowsInput, InputController

ROOT = Path(__file__).resolve().parents[1]


class JsonLines:
    def __init__(self):
        self.buffer = b''

    def feed(self, data):
        self.buffer += data
        if len(self.buffer) > 1024 * 1024:
            raise ValueError('Protocol frame exceeds limit')
        messages = []
        while b'\n' in self.buffer:
            line, self.buffer = self.buffer.split(b'\n', 1)
            try:
                obj = json.loads(line)
                if isinstance(obj, dict): messages.append(obj)
            except (ValueError, UnicodeError):
                logging.warning('Ignoring malformed JSON frame')
        return messages


def send(sock, obj):
    sock.sendall((json.dumps(obj, ensure_ascii=False) + '\n').encode('utf-8'))


def pair(sock):
    send(sock, {'type': 'pair', 'id': 'touchtruck'})


def states(snapshot):
    live = snapshot['connected']
    values = {name: ('On' if live and snapshot.get(name) else 'Off') for name in FLAGS}
    values.update({
        'connection': '已连接' if live and not snapshot['paused'] else ('游戏暂停' if live else '未连接'),
        'speed': f"{snapshot['speed']:.0f}" if live else '—',
        'fuel': f"{snapshot['fuel']:.0f}" if live else '—',
        'range': f"{snapshot['range']:.0f}" if live else '—',
        'cruise_speed': f"{snapshot['cruise_speed']:.0f}" if live and snapshot.get('cruise') else '—',
    })
    return values


def run(host='127.0.0.1', port=12136, *, input_controller=None, memory_reader=None,
        stop_event=None, reconnect_delay=1):
    controls = json.loads((ROOT / 'config/controls.json').read_text(encoding='utf-8'))
    actions = {f"touchtruck.action.{c['id']}": c for c in controls if c.get('keys')}
    if input_controller is None:
        backend = WindowsInput()
        input_controller = InputController(backend.send, backend.focused)
    inputs = input_controller
    memory = memory_reader if memory_reader is not None else SharedMemory()
    tracker = SnapshotTracker()
    stopping = False
    try:
        while not stopping and not (stop_event and stop_event.is_set()):
            try:
                with socket.create_connection((host, port), timeout=2) as sock:
                    sock.settimeout(1)
                    pair(sock)
                    parser, paired, last = JsonLines(), False, {}
                    was_live = False
                    logging.info('Connected to Touch Portal; waiting for pairing')
                    started = time.monotonic()
                    while not stopping and not (stop_event and stop_event.is_set()):
                        now = time.monotonic()
                        inputs.tick(now)
                        if not paired and now - started > 10:
                            raise ConnectionError('Plugin pairing timed out; import TouchTruck.tpp first')
                        ready, _, _ = select.select([sock], [], [], 0.04)
                        if ready:
                            data = sock.recv(65536)
                            if not data: raise ConnectionError('Touch Portal disconnected')
                            for msg in parser.feed(data):
                                kind = msg.get('type')
                                if kind == 'closePlugin':
                                    stopping = True
                                    break
                                if kind == 'info':
                                    paired = True
                                    logging.info('Plugin paired')
                                if kind == 'broadcast':
                                    inputs.release_all()
                                control = actions.get(msg.get('actionId'))
                                if paired and control:
                                    aid = control['id']
                                    if kind == 'up': inputs.up(aid)
                                    elif kind == 'down': inputs.down(aid, control['keys'], now)
                                    elif kind == 'action': inputs.down(aid, control['keys'], now, duration=0.1)
                        if not paired: continue
                        try:
                            data = memory.read()
                            snapshot = tracker.update(decode_snapshot(data), now) if data else disconnected()
                            if not snapshot['connected']:
                                memory.close()
                        except (OSError, ValueError) as exc:
                            logging.warning('Telemetry unavailable: %s', exc)
                            snapshot = disconnected()
                            memory.close()
                        values = states(snapshot)
                        if was_live and not snapshot['connected']:
                            inputs.release_all()
                        was_live = snapshot['connected']
                        for key, value in values.items():
                            if last.get(key) != value:
                                send(sock, {'type': 'stateUpdate', 'id': f'touchtruck.{key}', 'value': value})
                        last = values
            except (OSError, ValueError) as exc:
                logging.warning('Reconnecting: %s', exc)
            finally:
                inputs.release_all()
            if not stopping:
                if stop_event: stop_event.wait(reconnect_delay)
                else: time.sleep(reconnect_delay)
    finally:
        inputs.release_all()
        memory.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=12136)
    parser.add_argument('--probe', action='store_true')
    args = parser.parse_args()
    (ROOT / 'logs').mkdir(exist_ok=True)
    logging.basicConfig(level=logging.INFO, handlers=[RotatingFileHandler(ROOT / 'logs/bridge.log', maxBytes=1000000, backupCount=2, encoding='utf-8')], format='%(asctime)s %(levelname)s %(message)s')
    if args.probe:
        memory = SharedMemory()
        try:
            data = memory.read()
            print(json.dumps(decode_snapshot(data) if data else disconnected(), ensure_ascii=False, indent=2))
        finally: memory.close()
    else:
        # One bridge instance per Windows session.
        import ctypes
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.CreateMutexW.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_wchar_p]
        kernel.CreateMutexW.restype = ctypes.c_void_p
        kernel.CloseHandle.argtypes = [ctypes.c_void_p]
        mutex = kernel.CreateMutexW(None, False, 'Local\\TouchTruckBridge')
        if not mutex: raise ctypes.WinError(ctypes.get_last_error())
        if ctypes.get_last_error() == 183:
            kernel.CloseHandle(mutex)
            return
        try: run(args.host, args.port)
        except KeyboardInterrupt: pass
        finally: kernel.CloseHandle(mutex)


if __name__ == '__main__': main()
