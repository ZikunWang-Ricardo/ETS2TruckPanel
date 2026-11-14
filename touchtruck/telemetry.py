"""RenCloud V.1.12.1, revision 12: offsets from the vendored release header."""
import ctypes
import math
import struct
import time

SIZE = 32768
FLOATS = {'speed': 948, 'cruise_speed': 988, 'fuel': 1000, 'range': 1008}
FLAGS = {'parking': 1566, 'engine_brake': 1567, 'fuel_warning': 1570,
         'engine': 1576, 'wipers': 1577, 'left': 1580, 'right': 1581,
         'lights': 1583, 'high_beam': 1584, 'hazard': 1588, 'cruise': 1589,
         'diff_lock': 1608, 'axle': 1609, 'trailer': 6064}


def decode_snapshot(data: bytes) -> dict:
    if len(data) < SIZE:
        raise ValueError('Telemetry buffer is incomplete')
    revision = struct.unpack_from('<I', data, 40)[0]
    if revision != 12:
        raise ValueError(f'Unsupported telemetry revision {revision}; expected 12')
    game = struct.unpack_from('<I', data, 52)[0]
    if game not in (1, 2):
        raise ValueError('Unknown game')
    s = {'connected': bool(data[0]), 'paused': bool(data[4]),
         'timestamp': struct.unpack_from('<Q', data, 8)[0]}
    for name, offset in FLOATS.items():
        v = struct.unpack_from('<f', data, offset)[0]
        if not math.isfinite(v):
            raise ValueError(f'Invalid {name}')
        s[name] = abs(v) * 3.6 if name in ('speed', 'cruise_speed') else max(0, v)
    for name, offset in FLAGS.items():
        s[name] = bool(data[offset])
    return s


def disconnected():
    return dict(connected=False, paused=False, timestamp=None,
                **{k: None for k in FLOATS}, **{k: False for k in FLAGS})


class SnapshotTracker:
    def __init__(self, timeout=3):
        self.timeout = timeout
        self.last_timestamp = None
        self.changed_at = 0

    def update(self, snapshot, now=None):
        now = time.monotonic() if now is None else now
        if snapshot['timestamp'] != self.last_timestamp:
            self.last_timestamp = snapshot['timestamp']
            self.changed_at = now
        if not snapshot['connected'] or now - self.changed_at > self.timeout:
            return disconnected()
        return snapshot


class SharedMemory:
    """Open only existing read-only mapping; never create a fake mapping."""
    def __init__(self):
        self.kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        self.kernel.OpenFileMappingW.argtypes = [ctypes.c_uint, ctypes.c_int, ctypes.c_wchar_p]
        self.kernel.OpenFileMappingW.restype = ctypes.c_void_p
        self.kernel.MapViewOfFile.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_uint, ctypes.c_uint, ctypes.c_size_t]
        self.kernel.MapViewOfFile.restype = ctypes.c_void_p
        self.kernel.UnmapViewOfFile.argtypes = [ctypes.c_void_p]
        self.kernel.CloseHandle.argtypes = [ctypes.c_void_p]
        self.handle = self.ptr = None

    def read(self):
        if not self.handle:
            self.handle = self.kernel.OpenFileMappingW(4, False, 'Local\\SCSTelemetry')
            if not self.handle:
                return None
            self.ptr = self.kernel.MapViewOfFile(self.handle, 4, 0, 0, SIZE)
            if not self.ptr:
                self.close()
                return None
        # Retry if the producer changes its frame timestamp while copying.
        for _ in range(3):
            before = ctypes.string_at(self.ptr + 8, 8)
            data = ctypes.string_at(self.ptr, SIZE)
            after = ctypes.string_at(self.ptr + 8, 8)
            if before == after == data[8:16]:
                return data
        return None

    def close(self):
        if self.ptr:
            self.kernel.UnmapViewOfFile(self.ptr)
        if self.handle:
            self.kernel.CloseHandle(self.handle)
        self.ptr = self.handle = None
