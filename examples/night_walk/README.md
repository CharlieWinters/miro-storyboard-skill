# Night Walk: greybox with real GLBs

Spec generators behind the *Night Walk · Blender greybox demo* board
(https://miro.com/app/board/uXjVHh8qBX0=/).

- `street.py`: the shared street block (road, kerbs, pavements, varied
  building frontage with cornices, lamp posts via `repeat`, an end building)
  plus `write()` for a 16:9, 6 s, 1280-wide shot spec.
- `glbs.py`: the three Hunyuan 3D Pro GLBs (fal CDN URLs) and `glb()`, which
  sets real-world scale per asset (CHAR_A 1.68 m, CHAR_B 1.86 m, car 4.1 m).
- `s1.py`: Shot 1, the wide push-in. `S1.json` is its output.
- `s3.py`: Shot 3, the car passes and the camera whip-pans to follow it. `S3.json` is its output.
- `previews.py`: one grey turntable-style still per GLB for the reference library.

```bash
cd examples/night_walk && python3 s1.py
/Applications/Blender.app/Contents/MacOS/Blender -b \
  -P ../../scripts/blender_shot.py -- --spec S1.json --out /tmp/nightwalk
```
