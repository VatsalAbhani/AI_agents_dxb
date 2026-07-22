# Broker video — source

**Do NOT open film.html directly** — it's the renderer, not the video. It
needs the little server in this folder to save its output, and Chrome's
WebCodecs to encode.

## Rebuild the video (after editing scenes)
```bash
./make-video.sh
```
Output lands at `~/Desktop/guard-feedback-video.mp4` (~2 min render).

## Remixing
- Scenes live in `film.html` → the `SCENES` array (durations in frames,
  30fps; each scene is a draw(ctx, progress) function).
- Product frames: `shot-chat.png` / `shot-dash.png` — recapture with
  headless Chrome at `--window-size=500,975 --force-device-scale-factor=3`
  (headless viewport quirk: min width 500, titlebar steals 87px).
- `film.html?preview` renders a 9-tile still grid to `preview.png`
  instead of encoding — fast QA.
