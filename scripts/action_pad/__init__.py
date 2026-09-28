"""Action Pad: puppeteer greybox characters live with a gamepad (or keyboard).

Open a puppet shot (built by blender_shot.py from a spec whose rigged
subjects carry a "puppet" block) with:

    scripts/action_pad/open_action_pad.sh <shot.blend>

then View3D > Sidebar (N) > Action Pad. Controls while recording:

    left stick / WASD      walk, relative to the view
    right trigger / Shift  push into a run (analogue on a pad)
    left trigger / Ctrl    half speed
    A B X Y / 1 2 3 4      trigger the clip mapped to that button
    Start / Space          start or stop the take;  Esc stops too
    LB RB                  previous / next puppet (between takes)

Each take records one puppet from the start of the scene range while the
others play back, so a scene is built up in passes, like layering tracks.
"""

bl_info = {
    "name": "Action Pad",
    "author": "miro-storyboard",
    "version": (0, 1, 0),
    "blender": (4, 4, 0),
    "location": "View3D > Sidebar > Action Pad",
    "description": "Gamepad puppeteering for rigged greybox characters",
    "category": "Animation",
}

import json
import os
import socket
import subprocess
import sys
import time

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
for p in (HERE, os.path.dirname(HERE)):
    if p not in sys.path:
        sys.path.insert(0, p)

import puppet  # noqa: E402

PORT = 47811
PAD = {"state": {}, "stamp": 0.0, "name": ""}
_sock = None
_bridge = None
_recorder = None  # the running modal operator, if any


# --------------------------------------------------------------------------- #
# pad listener (always on while the add-on is loaded)
# --------------------------------------------------------------------------- #

def _poll_pad():
    global _sock
    if _sock is None:
        try:
            _sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            _sock.bind(("127.0.0.1", PORT))
            _sock.setblocking(False)
        except OSError:
            _sock = None
            return 1.0
    latest = None
    try:
        while True:
            latest, _ = _sock.recvfrom(4096)
    except (BlockingIOError, OSError):
        pass
    if latest:
        try:
            st = json.loads(latest.decode())
        except ValueError:
            st = None
        if st:
            prev = PAD["state"]
            PAD["state"], PAD["stamp"], PAD["name"] = st, time.time(), st.get("name", "gamepad")
            _pad_shortcuts(prev, st)
    return 1 / 60


def pad_live():
    return time.time() - PAD["stamp"] < 0.5


def _rising(prev, cur, key):
    return bool(cur.get(key)) and not bool(prev.get(key))


def _pad_shortcuts(prev, cur):
    """Start and the bumpers work even when no take is running."""
    if _recorder is not None:
        return
    s = bpy.context.scene
    props = getattr(s, "action_pad", None)
    if props is None:
        return
    if _rising(prev, cur, "lb") or _rising(prev, cur, "rb"):
        props.cycle_puppet(-1 if cur.get("lb") else 1)
    if _rising(prev, cur, "start"):
        _invoke_record()


def _invoke_record():
    wm = bpy.context.window_manager
    for win in wm.windows:
        for area in win.screen.areas:
            if area.type == "VIEW_3D":
                region = next(r for r in area.regions if r.type == "WINDOW")
                with bpy.context.temp_override(window=win, area=area, region=region):
                    bpy.ops.action_pad.record("INVOKE_DEFAULT")
                return


# --------------------------------------------------------------------------- #
# settings
# --------------------------------------------------------------------------- #

def _puppet_items(self, context):
    items = [(p.name, p.name, "") for p in puppet.puppets(context.scene)]
    return items or [("", "(no puppets in scene)", "")]


class ActionPadSettings(bpy.types.PropertyGroup):
    target: bpy.props.EnumProperty(name="Puppet", items=_puppet_items)
    speed_scale: bpy.props.FloatProperty(name="Speed", default=1.0, min=0.3, max=2.0,
                                         description="Scales walk and run pace")
    turn_rate: bpy.props.FloatProperty(name="Turn rate", default=220.0, min=45, max=720,
                                       description="Degrees per second the puppet can turn")
    relative: bpy.props.EnumProperty(name="Stick is relative to", default="VIEW",
                                     items=[("VIEW", "Viewport", "Up on the stick walks into the viewport"),
                                            ("CAMERA", "Shot camera", "Up walks into the shot camera"),
                                            ("WORLD", "World +Y", "Up walks along +Y")])
    proxy: bpy.props.BoolProperty(name="Stick figures while recording", default=True,
                                  description="Hide the heavy skinned meshes during a take so playback keeps up")
    out_dir: bpy.props.StringProperty(name="Output", subtype="DIR_PATH", default="//renders/")
    shot_name: bpy.props.StringProperty(name="Name", default="")

    def cycle_puppet(self, d):
        names = [p.name for p in puppet.puppets(bpy.context.scene)]
        if names:
            i = names.index(self.target) if self.target in names else 0
            self.target = names[(i + d) % len(names)]


# --------------------------------------------------------------------------- #
# operators
# --------------------------------------------------------------------------- #

KEYMAP_AXIS = {"W": ("ly", 1), "UP_ARROW": ("ly", 1), "S": ("ly", -1), "DOWN_ARROW": ("ly", -1),
               "D": ("lx", 1), "RIGHT_ARROW": ("lx", 1), "A": ("lx", -1), "LEFT_ARROW": ("lx", -1)}
KEYMAP_BUTTON = {"ONE": "a", "TWO": "b", "THREE": "x", "FOUR": "y", "NUMPAD_1": "a", "NUMPAD_2": "b",
                 "NUMPAD_3": "x", "NUMPAD_4": "y"}


def _cam_forward(context, mode):
    if mode == "VIEW" and context.region_data is not None:
        v = context.region_data.view_rotation @ Vector((0, 0, -1))
    elif mode == "CAMERA" and context.scene.camera is not None:
        v = context.scene.camera.matrix_world.to_3x3() @ Vector((0, 0, -1))
    else:
        return (0.0, 1.0)
    return (v.x, v.y) if abs(v.x) + abs(v.y) > 1e-4 else (0.0, 1.0)


class ACTIONPAD_OT_record(bpy.types.Operator):
    """Record a take for the selected puppet from the start of the scene range"""
    bl_idname = "action_pad.record"
    bl_label = "Record take"

    def invoke(self, context, event):
        global _recorder
        props = context.scene.action_pad
        root = context.scene.objects.get(props.target)
        if root is None or not root.get("ap_puppet"):
            self.report({"ERROR"}, "Pick a puppet first")
            return {"CANCELLED"}
        self.scene = context.scene
        self.take = puppet.Take(root, self.scene, props.speed_scale, props.turn_rate,
                                _cam_forward(context, props.relative))
        self.keys = {}
        self.pressed = {}
        self.prev_pad = dict(PAD["state"])
        self.last = time.perf_counter()
        self.hidden = []
        if props.proxy:
            for p in puppet.puppets(self.scene):
                arm = puppet.armature_of(p)
                for ch in arm.children:
                    if ch.type == "MESH" and not ch.hide_viewport:
                        ch.hide_viewport = True
                        self.hidden.append(ch)
                self.hidden.append((arm, arm.data.display_type, arm.show_in_front))
                arm.data.display_type, arm.show_in_front = "STICK", True
        self.scene.frame_set(self.scene.frame_start)
        wm = context.window_manager
        self.timer = wm.event_timer_add(1 / 60, window=context.window)
        wm.modal_handler_add(self)
        _recorder = self
        self.report({"INFO"}, f"Recording {root.name}: {'pad' if pad_live() else 'keyboard'}. "
                              "Space/Start/Esc to stop.")
        return {"RUNNING_MODAL"}

    def _input(self):
        inp = {"lx": 0.0, "ly": 0.0, "rt": 0.0, "lt": 0.0}
        for k, (axis, sign) in KEYMAP_AXIS.items():
            if self.keys.get(k):
                inp[axis] += sign
        if self.keys.get("LEFT_SHIFT") or self.keys.get("RIGHT_SHIFT"):
            inp["rt"] = 1.0
        if self.keys.get("LEFT_CTRL"):
            inp["lt"] = 1.0
        for k, b in KEYMAP_BUTTON.items():
            if self.keys.get(k):
                inp[b] = True
        if pad_live():
            st = PAD["state"]
            for a in ("lx", "ly", "rt", "lt"):
                if abs(st.get(a, 0.0)) > abs(inp[a]):
                    inp[a] = st.get(a, 0.0)
            for b in ("a", "b", "x", "y"):
                inp[b] = inp.get(b, False) or bool(st.get(b))
        return inp

    def modal(self, context, event):
        if event.type in KEYMAP_AXIS or event.type in KEYMAP_BUTTON or \
                event.type in ("LEFT_SHIFT", "RIGHT_SHIFT", "LEFT_CTRL"):
            self.keys[event.type] = event.value == "PRESS" or (event.value == "REPEAT")
            if event.value == "RELEASE":
                self.keys[event.type] = False
            return {"RUNNING_MODAL"}
        if event.type in ("ESC", "SPACE") and event.value == "PRESS":
            return self._stop(context)
        if event.type != "TIMER":
            return {"PASS_THROUGH"}
        cur = PAD["state"] if pad_live() else {}
        if _rising(self.prev_pad, cur, "start") or _rising(self.prev_pad, cur, "back"):
            return self._stop(context)
        self.prev_pad = dict(cur)
        now = time.perf_counter()
        dt, self.last = min(0.1, now - self.last), now
        more = self.take.tick(self._input(), dt)
        self.scene.frame_set(min(int(self.take.frame), self.scene.frame_end))
        return {"RUNNING_MODAL"} if more else self._stop(context)

    def _stop(self, context):
        global _recorder
        context.window_manager.event_timer_remove(self.timer)
        res = self.take.finish()
        for h in self.hidden:
            if isinstance(h, tuple):
                arm, disp, front = h
                arm.data.display_type, arm.show_in_front = disp, front
            else:
                h.hide_viewport = False
        _recorder = None
        self.scene.frame_set(self.scene.frame_start)
        trig = ", ".join(f"{t['clip']}@{t['frame']}" for t in res["triggers"]) or "none"
        self.report({"INFO"}, f"Take done: {res['puppet']} frames {res['frames'][0]}-{res['frames'][1]}, "
                              f"triggers: {trig}")
        return {"FINISHED"}


class ACTIONPAD_OT_clear(bpy.types.Operator):
    """Remove the selected puppet's recorded take (keys and triggered clips)"""
    bl_idname = "action_pad.clear"
    bl_label = "Clear take"

    def execute(self, context):
        s = context.scene
        root = s.objects.get(s.action_pad.target)
        if root is None:
            return {"CANCELLED"}
        arm = puppet.armature_of(root)
        puppet.clear_take(root, arm, s.frame_start, s.frame_end)
        home = root.get("ap_home")
        if home:
            puppet.write_frame(root, arm, puppet.new_state(home[0], home[1], home[3]), s.frame_start,
                               s.render.fps)
        return {"FINISHED"}


class ACTIONPAD_OT_bridge(bpy.types.Operator):
    """Start the gamepad bridge (pad_bridge.sh) in the background"""
    bl_idname = "action_pad.bridge"
    bl_label = "Connect gamepad"

    def execute(self, context):
        global _bridge
        if _bridge is not None and _bridge.poll() is None:
            self.report({"INFO"}, "Bridge already running")
            return {"FINISHED"}
        log = open(os.path.join(bpy.app.tempdir or "/tmp", "action_pad_bridge.log"), "w")
        _bridge = subprocess.Popen([os.path.join(HERE, "pad_bridge.sh")], stdout=log, stderr=log)
        self.report({"INFO"}, "Bridge starting. First run installs pygame (about a minute).")
        return {"FINISHED"}


class ACTIONPAD_OT_render(bpy.types.Operator):
    """Render <name>_block.png and <name>_move.mp4 for the storyboard"""
    bl_idname = "action_pad.render"
    bl_label = "Render grey clip"

    def execute(self, context):
        import blender_shot
        s = context.scene
        props = s.action_pad
        out = bpy.path.abspath(props.out_dir)
        os.makedirs(out, exist_ok=True)
        name = props.shot_name or s.get("shot_name", "TAKE")
        res = blender_shot.render_outputs(s, name, out)
        self.report({"INFO"}, f"Rendered {res.get('clip') or res.get('clip_error')}")
        return {"FINISHED"}


# --------------------------------------------------------------------------- #
# panel
# --------------------------------------------------------------------------- #

class ACTIONPAD_PT_panel(bpy.types.Panel):
    bl_label = "Action Pad"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Action Pad"

    def draw(self, context):
        s = context.scene
        props = s.action_pad
        col = self.layout.column()
        box = col.box()
        if pad_live():
            box.label(text=f"Pad: {PAD['name']}", icon="CHECKMARK")
        else:
            box.label(text="No pad. Keyboard: WASD, Shift, 1-4", icon="INFO")
            box.operator("action_pad.bridge", icon="PLUGIN")
        col.prop(props, "target")
        root = s.objects.get(props.target)
        if root is not None and root.get("ap_puppet"):
            arm = puppet.armature_of(root)
            table = puppet.clip_table(arm)
            b = col.box()
            for key, label in (("a", "A / 1"), ("b", "B / 2"), ("x", "X / 3"), ("y", "Y / 4")):
                clip = puppet.button_map(arm).get(key)
                if clip:
                    dur = table.get(clip, {}).get("duration", 0)
                    b.label(text=f"{label}:  {clip}  ({dur:.1f} s)")
            w, r = table.get("walk", {}), table.get("run", {})
            b.label(text=f"Walk {w.get('speed', 0):.2f} m/s, run {r.get('speed', 0):.2f} m/s")
        col.prop(props, "speed_scale")
        col.prop(props, "turn_rate")
        col.prop(props, "relative")
        col.prop(props, "proxy")
        row = col.row(align=True)
        row.scale_y = 1.6
        row.operator("action_pad.record", icon="REC")
        col.operator("action_pad.clear", icon="TRASH")
        col.separator()
        col.prop(props, "out_dir")
        col.prop(props, "shot_name")
        col.operator("action_pad.render", icon="RENDER_ANIMATION")


CLASSES = (ActionPadSettings, ACTIONPAD_OT_record, ACTIONPAD_OT_clear, ACTIONPAD_OT_bridge,
           ACTIONPAD_OT_render, ACTIONPAD_PT_panel)


def register():
    for c in CLASSES:
        bpy.utils.register_class(c)
    bpy.types.Scene.action_pad = bpy.props.PointerProperty(type=ActionPadSettings)
    if not bpy.app.timers.is_registered(_poll_pad):
        bpy.app.timers.register(_poll_pad, persistent=True)


def unregister():
    global _sock, _bridge
    if bpy.app.timers.is_registered(_poll_pad):
        bpy.app.timers.unregister(_poll_pad)
    if _sock is not None:
        _sock.close()
        _sock = None
    if _bridge is not None and _bridge.poll() is None:
        _bridge.terminate()
    del bpy.types.Scene.action_pad
    for c in reversed(CLASSES):
        bpy.utils.unregister_class(c)


if __name__ == "__main__":
    register()
