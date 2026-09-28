#!/usr/bin/env python3
"""Hold W, A, S, D for 0.75s each in a loop. F5 = start, F6 = stop, Ctrl+C = quit.

Linux:   evdev/uinput (works on Wayland and X11).
Windows: SendInput with scan codes via ctypes (no extra packages; works in most games).
"""
import sys
import threading
import time

HOLD_TIME = 0.75
KEYS = ["w", "a", "s", "d"]

running = threading.Event()
quit_flag = threading.Event()


def toggle(on):
    if on and not running.is_set():
        running.set()
        print("ON")
    elif not on and running.is_set():
        running.clear()
        print("OFF")


def press_loop(press, release):
    while not quit_flag.is_set():
        if not running.wait(timeout=0.1):
            continue
        for key in KEYS:
            if not running.is_set():
                break
            press(key)
            # Sleep in small steps so F6 stops quickly
            end = time.monotonic() + HOLD_TIME
            while running.is_set() and time.monotonic() < end:
                time.sleep(0.01)
            release(key)


# ---------------------------------------------------------------- Linux

def run_linux():
    import selectors

    import evdev
    from evdev import UInput, ecodes as e

    codes = {k: getattr(e, "KEY_" + k.upper()) for k in KEYS}

    kbds = []
    for path in evdev.list_devices():
        dev = evdev.InputDevice(path)
        caps = dev.capabilities().get(e.EV_KEY, [])
        if e.KEY_F5 in caps and e.KEY_F6 in caps:
            kbds.append(dev)
        else:
            dev.close()
    if not kbds:
        raise SystemExit("No keyboard found. Are you in the 'input' group?")

    ui = UInput({e.EV_KEY: list(codes.values())}, name="wasd-presser")

    def send(key, value):
        ui.write(e.EV_KEY, codes[key], value)
        ui.syn()

    worker = threading.Thread(
        target=press_loop,
        args=(lambda k: send(k, 1), lambda k: send(k, 0)),
        daemon=True,
    )
    worker.start()

    sel = selectors.DefaultSelector()
    for dev in kbds:
        sel.register(dev, selectors.EVENT_READ)

    print(f"Listening on: {', '.join(d.name for d in kbds)}")
    print("F5 = start, F6 = stop, Ctrl+C = quit")
    try:
        while True:
            for sel_key, _ in sel.select():
                for ev in sel_key.fileobj.read():
                    if ev.type != e.EV_KEY or ev.value != 1:
                        continue
                    if ev.code == e.KEY_F5:
                        toggle(True)
                    elif ev.code == e.KEY_F6:
                        toggle(False)
    except KeyboardInterrupt:
        pass
    finally:
        running.clear()
        quit_flag.set()
        worker.join(timeout=1)
        ui.close()


# -------------------------------------------------------------- Windows

def run_windows():
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.WinDLL("user32", use_last_error=True)

    ULONG_PTR = ctypes.c_size_t
    INPUT_KEYBOARD = 1
    KEYEVENTF_KEYUP = 0x0002
    KEYEVENTF_SCANCODE = 0x0008
    VK_F5, VK_F6 = 0x74, 0x75

    class KEYBDINPUT(ctypes.Structure):
        _fields_ = [("wVk", wintypes.WORD), ("wScan", wintypes.WORD),
                    ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD),
                    ("dwExtraInfo", ULONG_PTR)]

    class MOUSEINPUT(ctypes.Structure):
        _fields_ = [("dx", wintypes.LONG), ("dy", wintypes.LONG),
                    ("mouseData", wintypes.DWORD), ("dwFlags", wintypes.DWORD),
                    ("time", wintypes.DWORD), ("dwExtraInfo", ULONG_PTR)]

    class _INPUTUNION(ctypes.Union):
        _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT)]

    class INPUT(ctypes.Structure):
        _fields_ = [("type", wintypes.DWORD), ("u", _INPUTUNION)]

    # Scan codes (not virtual keys) so games using DirectInput see the presses
    scans = {k: user32.MapVirtualKeyW(ord(k.upper()), 0) for k in KEYS}

    def send(key, flags):
        inp = INPUT(type=INPUT_KEYBOARD)
        inp.u.ki = KEYBDINPUT(0, scans[key], KEYEVENTF_SCANCODE | flags, 0, 0)
        user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))

    worker = threading.Thread(
        target=press_loop,
        args=(lambda k: send(k, 0), lambda k: send(k, KEYEVENTF_KEYUP)),
        daemon=True,
    )
    worker.start()

    print("F5 = start, F6 = stop, Ctrl+C = quit")
    try:
        while True:
            if user32.GetAsyncKeyState(VK_F5) & 0x8000:
                toggle(True)
            elif user32.GetAsyncKeyState(VK_F6) & 0x8000:
                toggle(False)
            time.sleep(0.02)
    except KeyboardInterrupt:
        pass
    finally:
        running.clear()
        quit_flag.set()
        worker.join(timeout=1)


if __name__ == "__main__":
    if sys.platform == "win32":
        run_windows()
    elif sys.platform.startswith("linux"):
        run_linux()
    else:
        raise SystemExit(f"Unsupported platform: {sys.platform}")
