"""Scan-code input with focus checks, shared-key ownership and lost-up timeout."""
import ctypes
import logging
import time
from ctypes import wintypes


class InputController:
    def __init__(self, send_key, focused, max_hold=8):
        self.send_key = send_key
        self.focused = focused
        self.max_hold = max_hold
        self.held = {}
        self.deadlines = {}

    def down(self, action, keys, now=None, duration=None):
        if action in self.held or not self.focused() or not keys:
            return
        now = time.monotonic() if now is None else now
        existing = {k for entry in self.held.values() for k in entry}
        pressed = []
        try:
            for k in keys:
                if k not in existing:
                    self.send_key(k, True)
                    pressed.append(k)
        except Exception:
            for k in reversed(pressed):
                self.send_key(k, False)
            raise
        self.held[action] = list(keys)
        self.deadlines[action] = now + (self.max_hold if duration is None else duration)

    def up(self, action):
        keys = self.held.pop(action, [])
        self.deadlines.pop(action, None)
        other = {k for entry in self.held.values() for k in entry}
        failed = []
        for k in reversed(keys):
            if k not in other:
                try:
                    self.send_key(k, False)
                except OSError:
                    logging.exception('Key release failed for scan code %s; will retry', k)
                    failed.append(k)
        if failed:
            self.held[action] = [k for k in keys if k in failed]
            self.deadlines[action] = 0

    def tick(self, now=None):
        now = time.monotonic() if now is None else now
        if not self.focused():
            self.release_all()
        else:
            for action, deadline in list(self.deadlines.items()):
                if now >= deadline:
                    self.up(action)

    def release_all(self):
        for action in list(self.held):
            self.up(action)


class WindowsInput:
    def __init__(self):
        self.user = ctypes.WinDLL('user32', use_last_error=True)
        self.kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        class KEYBDINPUT(ctypes.Structure):
            _fields_ = [('wVk', wintypes.WORD), ('wScan', wintypes.WORD),
                        ('dwFlags', wintypes.DWORD), ('time', wintypes.DWORD),
                        ('dwExtraInfo', ctypes.c_size_t)]
        class MOUSEINPUT(ctypes.Structure):
            _fields_ = [('dx', wintypes.LONG), ('dy', wintypes.LONG),
                        ('mouseData', wintypes.DWORD), ('dwFlags', wintypes.DWORD),
                        ('time', wintypes.DWORD), ('dwExtraInfo', ctypes.c_size_t)]
        class UNION(ctypes.Union):
            _fields_ = [('ki', KEYBDINPUT), ('mi', MOUSEINPUT)]
        class INPUT(ctypes.Structure):
            _anonymous_ = ('u',)
            _fields_ = [('type', wintypes.DWORD), ('u', UNION)]
        self.INPUT, self.KEYBDINPUT = INPUT, KEYBDINPUT
        self.user.SendInput.argtypes = [wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int]
        self.user.SendInput.restype = wintypes.UINT
        self.user.GetForegroundWindow.restype = wintypes.HWND
        self.user.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
        self.kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        self.kernel.OpenProcess.restype = wintypes.HANDLE
        self.kernel.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
        self.kernel.CloseHandle.argtypes = [wintypes.HANDLE]

    def focused(self):
        pid = wintypes.DWORD()
        self.user.GetWindowThreadProcessId(self.user.GetForegroundWindow(), ctypes.byref(pid))
        handle = self.kernel.OpenProcess(0x1000, False, pid.value)
        if not handle:
            return False
        try:
            name = ctypes.create_unicode_buffer(2048)
            size = wintypes.DWORD(len(name))
            ok = self.kernel.QueryFullProcessImageNameW(handle, 0, name, ctypes.byref(size))
            return bool(ok and name.value.lower().endswith(('\\eurotrucks2.exe', '\\amtrucks.exe')))
        finally:
            self.kernel.CloseHandle(handle)

    def send(self, scan, down):
        event = self.INPUT(type=1)
        event.ki = self.KEYBDINPUT(0, scan & 0xff, 8 | (0 if down else 2) | (1 if scan > 255 else 0), 0, 0)
        if self.user.SendInput(1, ctypes.byref(event), ctypes.sizeof(event)) != 1:
            raise OSError('SendInput failed; check game/bridge privilege levels')
