#!/usr/bin/env python3
"""RCW Cloud Video Renderer library. Renders video_script.json -> output.mp4."""
import json, os, subprocess, sys

def log(m): print(f"[renderer] {m}", flush=True)

def main():
    script_path = os.environ.get("SCRIPT_PATH", "video_script.json")
    if not os.path.exists(script_path):
        sys.exit("video_script.json not found")
    script = json.load(open(script_path, encoding="utf-8"))
    title = script.get("title", "RCW IT Training Lab")
    slides = script.get("slides", [])
    if not slides: sys.exit("no slides")
    log(f"Rendering '{title}' with {len(slides)} slides")

    from PIL import Image, ImageDraw, ImageFont
    os.makedirs("slides", exist_ok=True)
    fonts = [f for f in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                          "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"] if os.path.exists(f)]
    def font(sz):
        if fonts:
            try: return ImageFont.truetype(fonts[0], sz)
            except Exception: pass
        return ImageFont.load_default()
    W,H = 1280,720
    for i,s in enumerate(slides):
        img = Image.new("RGB",(W,H),"#061633"); d=ImageDraw.Draw(img)
        d.rectangle([0,0,W,12],fill="#ffd51d")
        d.text((60,70),s.get("heading","Slide"),font=font(54),fill="#ffffff")
        y=170
        for line in (s.get("body","") or "").split("\n"):
            line=line.strip()
            if not line: y+=30; continue
            while len(line)>62:
                d.text((60,y),line[:62],font=font(28),fill="#dbe7ff"); line=line[62:]; y+=40
            d.text((60,y),line,font=font(28),fill="#dbe7ff"); y+=40
        d.text((60,H-55),"RCW IT Training - www.rcwittraining.in",font=font(24),fill="#4bd7ff")
        img.save(f"slides/slide_{i:03d}.png")
        log(f"RENDER_PROGRESS={int((i+1)/len(slides)*50)}")  # slides = first 50%
    log("slides rendered")

    os.makedirs("audio",exist_ok=True)
    # Natural voice via edge-tts (free, Microsoft neural voices). Voice configurable.
    voice = os.environ.get("TTS_VOICE", "en-US-JennyNeural")
    rate  = os.environ.get("TTS_RATE", "+0%")
    for i,s in enumerate(slides):
        text=(s.get("narration") or s.get("body") or s.get("heading") or "").strip()
        if not text: continue
        wav=f"audio/slide_{i:03d}.mp3"
        # edge-tts outputs mp3; we convert to wav for ffmpeg concat later
        subprocess.run(["edge-tts","--voice",voice,"--rate",rate,"--text",text,"--write-media",wav],check=False)
        log(f"RENDER_PROGRESS={50 + int((i+1)/len(slides)*25)}")  # audio = next 25%
        if not os.path.exists(wav) or os.path.getsize(wav)<100:
            log(f"  edge-tts failed for slide {i}, using silent gap")
            subprocess.run(["ffmpeg","-y","-f","lavfi","-i","anullsrc=r=22050:cl=mono","-t","6",wav],check=False)
    log("audio generated (edge-tts natural voice)")

    segs=[]
    for i,s in enumerate(slides):
        wav=f"audio/slide_{i:03d}.mp3"; dur=7.0
        if os.path.exists(wav):
            out=subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1",wav],capture_output=True,text=True).stdout.strip()
            try: dur=float(out)+0.8
            except Exception: dur=7.0
        segs.append({"img":f"slides/slide_{i:03d}.png","wav":wav,"dur":dur})

    # Inputs: first all slide images (video), then all narration wavs (audio)
    video_count = len(segs)
    inputs=[]
    for seg in segs: inputs += ["-loop","1","-i",seg["img"]]
    for seg in segs:
        if os.path.exists(seg["wav"]): inputs += ["-i",seg["wav"]]
    audio_inputs=[i for i,seg in enumerate(segs) if os.path.exists(seg["wav"])]

    # Video filter: each image -> timed clip, then concat
    vf=[]
    for i in range(video_count):
        vf.append(f"[{i}:v]scale=1280:720,setsar=1,trim=duration={segs[i]['dur']:.3f},setpts=PTS-STARTPTS[v{i}]")
    vf.append("".join(f"[v{i}]" for i in range(video_count)) + f"concat=n={video_count}:v=1:a=0[vout]")

    filters = ";".join(vf)

    # Audio filter: audio inputs are at indices video_count + k (0-based among audio inputs)
    if audio_inputs:
        af=[]
        for k, i in enumerate(audio_inputs):
            af.append(f"[{video_count + k}:a]aresample=22050,atrim=0:{segs[i]['dur']:.3f},asetpts=PTS-STARTPTS[a{k}]")
        af.append("".join(f"[a{k}]" for k in range(len(audio_inputs))) + f"concat=n={len(audio_inputs)}:v=0:a=1[aout]")
        filters += ";" + ";".join(af)

    cmd=["ffmpeg","-y"] + inputs + ["-filter_complex", filters, "-map","[vout]"]
    if audio_inputs:
        cmd += ["-map","[aout]"]
    cmd += ["-c:v","libx264","-preset","veryfast","-crf","23","-pix_fmt","yuv420p",
            "-c:a","aac","-b:a","128k","-shortest","output.mp4"]
    log("RENDER_PROGRESS=75")
    log("running ffmpeg...")
    r=subprocess.run(cmd,capture_output=True,text=True)
    if r.returncode!=0:
        log("ffmpeg error: "+r.stderr[-1200:]); sys.exit("ffmpeg failed")
    log("RENDER_PROGRESS=100")
    log("DONE - output.mp4")
    log("DONE - output.mp4")

if __name__=="__main__":
    main()
