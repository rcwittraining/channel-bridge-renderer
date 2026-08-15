# RCW Cloud Video Renderer

Turns a `video_script.json` (title + slides with narration) into a finished MP4
(1280x720, slides + AI voiceover) with **no size/length limit** — runs on
GitHub Actions cloud runners (free minutes), not on a phone.

## How it works
1. The mobile app (channel-bridge) sends the script (base64) to this repo's
   **"Render Lab Video"** workflow (workflow_dispatch).
2. The runner: installs ffmpeg + espeak-ng → renders each slide as PNG →
   synthesizes narration per slide → concatenates into output.mp4.
3. The MP4 is uploaded as a workflow **artifact** (7-day retention) — download
   and upload to YouTube, or extend with the YouTube API for direct upload.

## Files
- `.github/workflows/render.yml` — the workflow
- `renderer_lib.py` — the renderer (tested: 3 slides → 21s MP4, h264+aac)

## Manual run
    echo '{"title":"...","slides":[{"heading":"..","body":"..","narration":".."}]}' | base64 > /tmp/b64.txt
    # paste into workflow input "script"
