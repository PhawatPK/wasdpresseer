#!/usr/bin/env python3
"""Hold W, A, S, D for 0.75s each in a loop. F5 = start, F6 = stop, Ctrl+C = quit.

Uses evdev/uinput so it works on Wayland (global hotkeys + key injection).
"""
import selectors
import threading
import time

import evdev
from evdev import UInput, ecodes as e

HOLD_TIME = 0.75
KEYS = [e.KEY_W, e.KEY_A, e.KEY_S, e.KEY_D]

running = threading.Event()
quit_flag = threading.Event()


def find_keyboards():
    kbds = []
    for path in evdev.list_devices():
        dev = evdev.InputDevice(path)
        caps = dev.capabilities().get(e.EV_KEY, [])
        if e.KEY_F5 in caps and e.KEY_F6 in caps:
            kbds.append(dev)
        else:
            dev.close()
    return kbds


def press_loop(ui):
    while not quit_flag.is_set():
        if not running.wait(timeout=0.1):
            continue
        for key in KEYS:
            if not running.is_set():
                break
            ui.write(e.EV_KEY, key, 1)
            ui.syn()
            # Sleep in small steps so F6 stops quickly
            end = time.monotonic() + HOLD_TIME
            while running.is_set() and time.monotonic() < end:
                time.sleep(0.01)
            ui.write(e.EV_KEY, key, 0)
            ui.syn()


def main():
    kbds = find_keyboards()
    if not kbds:
        raise SystemExit("No keyboard found. Are you in the 'input' group?")

    ui = UInput({e.EV_KEY: KEYS}, name="wasd-presser")
    worker = threading.Thread(target=press_loop, args=(ui,), daemon=True)
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
                    if ev.code == e.KEY_F5 and not running.is_set():
                        running.set()
                        print("ON")
                    elif ev.code == e.KEY_F6 and running.is_set():
                        running.clear()
                        print("OFF")
    except KeyboardInterrupt:
        pass
    finally:
        running.clear()
        quit_flag.set()
        worker.join(timeout=1)
        ui.close()


if __name__ == "__main__":
    main()
