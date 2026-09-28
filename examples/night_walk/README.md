# Night Walk: greybox with real GLBs

Spec generators behind the *Night Walk · Blender greybox demo* board
(https://miro.com/app/board/uXjVHh8qBX0=/).

- `street.py`: the shared street block (road, kerbs, pavements, varied
  building frontage with cornices, lamp posts via `repeat`, an end building)
  plus `write()` for a 16:9, 6 s, 1280-wide shot spec.
- `glbs.py`: the three Hunyuan 3D Pro GLBs (fal CDN URLs) and `glb()`, which
  sets real-world scale per asset (CHAR_A 1.68 m, CHAR_B 1.86 m, car 4.1 m);
  plus the Meshy rigs, the four Hunyuan Motion clips, and `rigged()`.
- `s1.py`: Shot 1, the wide push-in. `S1.json` is its output.
- `s3.py`: Shot 3, the car passes and the camera whip-pans to follow it. `S3.json` is its output.
- `s2.py`: Shot 2, a tracking two-shot with both characters rigged and walking (Hunyuan Motion). `S2.json` is its output.
- `s4.py`: Shot 4, the reaction close-up: both stop, she turns to follow the passing car, he flinches a beat later. `S4.json` is its output.
- `s_puppet.py`: the Action Pad stage, both characters as gamepad puppets (see `scripts/action_pad/README.md`). `demo_takes.json` is a scripted two-pass take for it.
- `previews.py`: one grey turntable-style still per GLB for the reference library.

```bash
cd examples/night_walk && python3 s1.py
/Applications/Blender.app/Contents/MacOS/Blender -b \
  -P ../../scripts/blender_shot.py -- --spec S1.json --out /tmp/nightwalk
```
