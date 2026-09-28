"""Read a gamepad and stream its state to Blender's Action Pad over UDP.

Blender has no gamepad input, so this small helper does it with SDL (via
pygame) and sends the state 60 times a second to 127.0.0.1:47811. Xbox,
PlayStation, Switch Pro and 8BitDo pads all come through SDL's standard
controller layout, so the button names below mean the same on every pad
(A = bottom face button, B = right, X = left, Y = top).

    ./pad_bridge.sh          # makes a venv with pygame on first run

Packet (JSON): lx, ly (left stick, +ly = up), rx, ry, lt, rt (0..1),
a, b, x, y, lb, rb, start, back (bools), name.
"""

import json
import socket
import sys
import time

import pygame

PORT = 47811
DEST = ("127.0.0.1", PORT)


def open_controller():
    try:
        from pygame._sdl2 import controller as ctl
    except ImportError:
        ctl = None
    if ctl is not None:
        ctl.init()
        for i in range(ctl.get_count()):
            if ctl.is_controller(i):
                return "controller", ctl.Controller(i)
    pygame.joystick.init()
    if pygame.joystick.get_count():
        j = pygame.joystick.Joystick(0)
        j.init()
        return "joystick", j
    return None, None


def read_controller(c):
    from pygame._sdl2 import controller as ctl  # noqa: F401
    ax = lambda a: c.get_axis(a) / 32767.0  # noqa: E731
    return {
        "lx": ax(pygame.CONTROLLER_AXIS_LEFTX), "ly": -ax(pygame.CONTROLLER_AXIS_LEFTY),
        "rx": ax(pygame.CONTROLLER_AXIS_RIGHTX), "ry": -ax(pygame.CONTROLLER_AXIS_RIGHTY),
        "lt": max(0.0, ax(pygame.CONTROLLER_AXIS_TRIGGERLEFT)),
        "rt": max(0.0, ax(pygame.CONTROLLER_AXIS_TRIGGERRIGHT)),
        "a": c.get_button(pygame.CONTROLLER_BUTTON_A), "b": c.get_button(pygame.CONTROLLER_BUTTON_B),
        "x": c.get_button(pygame.CONTROLLER_BUTTON_X), "y": c.get_button(pygame.CONTROLLER_BUTTON_Y),
        "lb": c.get_button(pygame.CONTROLLER_BUTTON_LEFTSHOULDER),
        "rb": c.get_button(pygame.CONTROLLER_BUTTON_RIGHTSHOULDER),
        "start": c.get_button(pygame.CONTROLLER_BUTTON_START),
        "back": c.get_button(pygame.CONTROLLER_BUTTON_BACK),
    }


def read_joystick(j):
    # Raw-joystick fallback: Xbox-style axis/button order, the commonest.
    g = lambda i: j.get_axis(i) if i < j.get_numaxes() else 0.0  # noqa: E731
    b = lambda i: bool(j.get_button(i)) if i < j.get_numbuttons() else False  # noqa: E731
    return {"lx": g(0), "ly": -g(1), "rx": g(2), "ry": -g(3),
            "lt": max(0.0, (g(4) + 1) / 2), "rt": max(0.0, (g(5) + 1) / 2),
            "a": b(0), "b": b(1), "x": b(2), "y": b(3), "lb": b(4), "rb": b(5),
            "start": b(7), "back": b(6)}


def main():
    pygame.init()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    kind, dev, name, last_scan = None, None, "", 0.0
    print(f"Action Pad bridge -> udp://{DEST[0]}:{PORT}. Ctrl-C to stop.")
    while True:
        pygame.event.pump()
        if dev is None and time.time() - last_scan > 2.0:
            last_scan = time.time()
            kind, dev = open_controller()
            if dev is not None:
                name = dev.name if kind == "controller" else dev.get_name()
                print(f"Connected: {name} ({kind})")
            else:
                print("Waiting for a controller (pair it in System Settings > Bluetooth)...", end="\r")
        if dev is not None:
            try:
                state = read_controller(dev) if kind == "controller" else read_joystick(dev)
            except pygame.error:
                print(f"\nLost {name}")
                kind, dev = None, None
                continue
            state = {k: (bool(v) if isinstance(v, (int, bool)) and k not in
                         ("lx", "ly", "rx", "ry", "lt", "rt") else round(float(v), 3))
                     for k, v in state.items()}
            state["name"] = name
            sock.sendto(json.dumps(state).encode(), DEST)
        time.sleep(1 / 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
