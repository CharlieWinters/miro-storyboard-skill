"""The puppet engine: controller input in, keyframes out.

A puppet is a root empty (position + heading, keyed per frame) with a
Meshy-rigged armature under it whose NLA stack is:

    AP_REACT*  triggered clips (flinch, wave...), blended in and out
    AP_RUN     run cycle, influence = how far past walking pace we are
    AP_WALK    walk cycle, influence = how far toward walking pace we are
    AP_IDLE    idle clip, always under everything

Walk and run are driven by *animated strip time*: the cycle advances by the
distance actually covered divided by the cycle's own stride, so the feet
stay planted at any speed. The movement logic (`step`) is plain Python with
no bpy, so the same code runs live from a gamepad and headless from a
scripted take.
"""

import json
import math

import bpy

DEADZONE = 0.15


# --------------------------------------------------------------------------- #
# pure logic
# --------------------------------------------------------------------------- #

def new_state(x, y, heading):
    return {"x": x, "y": y, "heading": heading, "speed": 0.0, "phase": 0.0, "t": 0.0,
            "react_until": -1.0, "walk_w": 0.0, "run_w": 0.0}


def _stick(lx, ly):
    m = math.hypot(lx, ly)
    if m < DEADZONE:
        return 0.0, 0.0, 0.0
    k = min(1.0, (m - DEADZONE) / (1 - DEADZONE)) / m
    return lx * k, ly * k, min(1.0, m * k)


def step(state, inp, dt, p, cam_fwd=(0.0, 1.0)):
    """Advance one tick. `inp` holds lx, ly (stick, +ly = forward), rt, lt (0..1).

    `p` = {walk_speed, walk_dist, run_speed, run_dist, speed_scale,
    turn_rate} (m/s, m, deg/s). Stick direction is relative to `cam_fwd`,
    the camera's forward vector on the ground, so "up" walks into the shot.
    """
    s = dict(state)
    lx, ly, mag = _stick(inp.get("lx", 0.0), inp.get("ly", 0.0))
    reacting = s["t"] < s["react_until"]

    walk_v, run_v = p["walk_speed"], max(p["run_speed"], p["walk_speed"] + 1e-3)
    if reacting or mag == 0.0:
        target = 0.0
    else:
        target = mag * (walk_v + inp.get("rt", 0.0) * (run_v - walk_v)) * p.get("speed_scale", 1.0)
        if inp.get("lt", 0.0) > 0.5:
            target *= 0.5
    rate = 3.0 if target > s["speed"] else 4.5  # m/s^2: people stop quicker than they start
    s["speed"] += max(-rate * dt, min(rate * dt, target - s["speed"]))

    if mag > 0.0 and not reacting:
        fx, fy = cam_fwd
        n = math.hypot(fx, fy) or 1.0
        fx, fy = fx / n, fy / n
        rx, ry = fy, -fx  # camera right on the ground
        dx, dy = fx * ly + rx * lx, fy * ly + ry * lx
        want = math.atan2(dx, -dy)  # the rig faces -Y at heading 0
        diff = (want - s["heading"] + math.pi) % (2 * math.pi) - math.pi
        turn = math.radians(p.get("turn_rate", 220.0)) * dt
        s["heading"] += max(-turn, min(turn, diff))

    h = s["heading"]
    s["x"] += math.sin(h) * s["speed"] * dt
    s["y"] += -math.cos(h) * s["speed"] * dt

    s["walk_w"] = min(1.0, s["speed"] / walk_v) if walk_v > 0 else 0.0
    s["run_w"] = max(0.0, min(1.0, (s["speed"] - walk_v) / (run_v - walk_v)))
    dist = p["walk_dist"] + s["run_w"] * (p["run_dist"] - p["walk_dist"])
    s["phase"] += s["speed"] * dt / max(dist, 1e-3)
    s["t"] += dt
    return s


# --------------------------------------------------------------------------- #
# the rig side
# --------------------------------------------------------------------------- #

def puppets(scene=None):
    scene = scene or bpy.context.scene
    return [o for o in scene.objects if o.get("ap_puppet")]


def armature_of(root):
    return bpy.data.objects.get(root.get("ap_arm", ""))


def clip_table(arm):
    return json.loads(arm.get("ap_clips", "{}"))


def button_map(arm):
    return json.loads(arm.get("ap_buttons", "{}"))


def params_for(arm, speed_scale=1.0, turn_rate=220.0):
    t = clip_table(arm)
    walk = t.get("walk", {"speed": 1.3, "distance": 1.35})
    run = t.get("run", walk)
    return {"walk_speed": walk["speed"], "walk_dist": walk["distance"],
            "run_speed": run["speed"], "run_dist": run["distance"],
            "speed_scale": speed_scale, "turn_rate": turn_rate}


def _track(ad, name):
    tr = ad.nla_tracks.get(name)
    if tr is None:
        tr = ad.nla_tracks.new()
        tr.name = name
    return tr


def _looping_strip(track, name, action, frame_start):
    st = track.strips.new(name, int(frame_start), action)
    st.repeat = 400  # effectively endless; animated strip time picks the pose
    st.use_animated_time = True
    st.use_animated_influence = True
    st.extrapolation = "HOLD"
    return st


def setup_puppet(root, arm, scene=None):
    """Build the NLA stack for a rig whose clip library already exists."""
    scene = scene or bpy.context.scene
    table = clip_table(arm)
    ad = arm.animation_data_create()
    ad.action = None
    for tr in list(ad.nla_tracks):
        ad.nla_tracks.remove(tr)
    start = scene.frame_start
    for key, track in (("idle", "AP_IDLE"), ("walk", "AP_WALK"), ("run", "AP_RUN")):
        if key in table:
            _looping_strip(_track(ad, track), key, bpy.data.actions[table[key]["action"]], start)
    _track(ad, "AP_REACT")
    root["ap_puppet"] = True
    root["ap_arm"] = arm.name
    root["ap_home"] = [root.location.x, root.location.y, root.location.z, root.rotation_euler.z]
    # A standing, idling pose on frame 1 even before any take is recorded.
    write_frame(root, arm, new_state(root.location.x, root.location.y, root.rotation_euler.z),
                start, scene.render.fps)


def _strip(arm, track):
    ad = arm.animation_data
    tr = ad.nla_tracks.get(track) if ad else None
    return tr.strips[0] if tr and len(tr.strips) else None


def write_frame(root, arm, s, frame, fps):
    """Key the root and the locomotion strips for one frame of state `s`."""
    table = clip_table(arm)
    root.location.x, root.location.y = s["x"], s["y"]
    root.rotation_euler.z = s["heading"]
    root.keyframe_insert("location", frame=frame)
    root.keyframe_insert("rotation_euler", index=2, frame=frame)
    for key, track, w, clock in (("walk", "AP_WALK", s["walk_w"], s["phase"]),
                                 ("run", "AP_RUN", s["run_w"], s["phase"]),
                                 ("idle", "AP_IDLE", 1.0, None)):
        st = _strip(arm, track)
        if st is None:
            continue
        c = table[key]
        span = c["end"] - c["start"]
        # Walk/run advance by distance covered (phase, in cycles); idle by time.
        st.strip_time = c["start"] + (clock * span if clock is not None else s["t"] * fps % span)
        st.influence = w
        st.keyframe_insert("strip_time", frame=frame)
        st.keyframe_insert("influence", frame=frame)


def trigger(arm, clip, frame, fps):
    """Drop `clip` onto the react layer at `frame`. Returns its duration (s)."""
    table = clip_table(arm)
    c = table[clip]
    act = bpy.data.actions[c["action"]]
    length = c["end"] - c["start"]
    ad = arm.animation_data
    tracks = [t for t in ad.nla_tracks if t.name.startswith("AP_REACT")]
    lo, hi = frame, frame + length
    track = next((t for t in tracks
                  if all(st.frame_end < lo or st.frame_start > hi for st in t.strips)), None)
    if track is None:  # overlapping reactions stack on their own layer
        track = ad.nla_tracks.new()
        track.name = f"AP_REACT.{len(tracks)}"
    st = track.strips.new(f"{clip}@{int(frame)}", int(frame), act)
    blend = c.get("blend", 0.3) * fps
    st.blend_in = st.blend_out = min(blend, length / 3)
    st.extrapolation = "NOTHING"
    return length / fps


def linearise(root, arm):
    """Per-frame keys want LINEAR, or Bezier overshoot wobbles the root."""
    from library import _action_fcurves
    ad = root.animation_data
    fcs = _action_fcurves(ad.action) if ad and ad.action else []
    for tr in (arm.animation_data.nla_tracks if arm.animation_data else []):
        for st in tr.strips:
            fcs.extend(st.fcurves)
    for fc in fcs:
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"


def clear_take(root, arm, f0, f1):
    """Remove one puppet's recorded keys and triggered clips in [f0, f1]."""
    from library import _action_fcurves
    ad = root.animation_data
    fcs = _action_fcurves(ad.action) if ad and ad.action else []
    for tr in (arm.animation_data.nla_tracks if arm.animation_data else []):
        if tr.name.startswith("AP_REACT"):
            for st in [st for st in tr.strips if f0 <= st.frame_start <= f1]:
                tr.strips.remove(st)
        else:
            for st in tr.strips:
                fcs.extend(st.fcurves)
    for fc in fcs:
        for kp in reversed(list(fc.keyframe_points)):
            if f0 <= kp.co.x <= f1:
                fc.keyframe_points.remove(kp)


class Take:
    """One recording pass for one puppet: feed ticks, get keys.

    Used by the live modal operator (real clock, gamepad) and by
    script_take.py (fixed clock, scripted input); both share this class.
    """

    def __init__(self, root, scene, speed_scale=1.0, turn_rate=220.0, cam_fwd=(0.0, 1.0)):
        self.root, self.arm, self.scene = root, armature_of(root), scene
        self.fps = scene.render.fps
        self.params = params_for(self.arm, speed_scale, turn_rate)
        self.buttons = button_map(self.arm)
        self.cam_fwd = cam_fwd
        home = root.get("ap_home") or [root.location.x, root.location.y, root.location.z, 0.0]
        root.location.z = home[2]
        self.state = new_state(home[0], home[1], home[3])
        self.f0 = scene.frame_start
        self.next_frame = self.f0
        self.prev_buttons = {}
        self.log = []
        clear_take(root, self.arm, self.f0, scene.frame_end)

    @property
    def frame(self):
        return self.f0 + self.state["t"] * self.fps

    def tick(self, inp, dt):
        """Advance by dt seconds of input; returns False when the range is used up."""
        for b, clip in self.buttons.items():
            down = bool(inp.get(b))
            if down and not self.prev_buttons.get(b) and clip in clip_table(self.arm) \
                    and self.state["t"] >= self.state["react_until"]:
                f = int(round(self.frame))
                dur = trigger(self.arm, clip, f, self.fps)
                self.state["react_until"] = self.state["t"] + dur * 0.6
                self.log.append({"t": round(self.state["t"], 2), "frame": f, "clip": clip})
            self.prev_buttons[b] = down
        self.state = step(self.state, inp, dt, self.params, self.cam_fwd)
        while self.next_frame <= min(self.frame, self.scene.frame_end):
            write_frame(self.root, self.arm, self.state, self.next_frame, self.fps)
            self.next_frame += 1
        return self.next_frame <= self.scene.frame_end

    def finish(self):
        linearise(self.root, self.arm)
        return {"puppet": self.root.name, "frames": [self.f0, self.next_frame - 1],
                "end": [round(self.state["x"], 2), round(self.state["y"], 2)], "triggers": self.log}
