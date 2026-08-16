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
    def font(sz, bold=True):
        if fonts:
            try: return ImageFont.truetype(fonts[0], sz)
            except Exception: pass
        return ImageFont.load_default()
    W,H = 1280,720

    def draw_step_circle(d, cx, cy, num, r=26):
        """Numbered pulsing 'click here' circle."""
        d.ellipse([cx-r,cy-r,cx+r,cy+r], fill="#e86f0c")
        d.ellipse([cx-r+6,cy-r+6,cx+r-6,cy+r-6], fill="#ffffff")
        d.text((cx,cy), str(num), font=font(26,bold=True), fill="#e86f0c", anchor="mm")

    def draw_ui_slide(d, s):
        ui = s.get("ui") or {}
        utype = ui.get("type", "windows")
        title = ui.get("title") or s.get("heading", "Settings")
        items = ui.get("items") or []
        steps = ui.get("steps") or []
        x0, y0, x1, y1 = 60, 150, W-60, H-90

        if utype == "windows":
            # Windows 11 style settings window (light)
            d.rounded_rectangle([x0,y0,x1,y1], radius=14, fill="#ffffff", outline="#d5dbe1", width=3)
            d.rounded_rectangle([x0,y0,x1,y0+48], radius=14, fill="#f3f3f3", outline="#d5dbe1", width=3)
            d.ellipse([x0+18,y0+16,x0+34,y0+32], fill="#ff5f57")
            d.ellipse([x0+42,y0+16,x0+58,y0+32], fill="#febc2e")
            d.ellipse([x0+66,y0+16,x0+82,y0+32], fill="#28c840")
            d.text((x0+100,y0+10), title, font=font(24), fill="#1a1a1a")
            # left sidebar
            d.rectangle([x0,y0+48,x0+250,y1], fill="#f3f3f3")
            d.rectangle([x0,y0+48,x0+250,y1], outline="#d5dbe1", width=2)
            nav = ["System","Bluetooth & devices","Network & internet","Personalization","Apps","Accounts","Time & language","Storage","Accessibility"]
            ny = y0+70
            for i, n in enumerate(nav):
                fill = "#e8f1fb" if i==0 else None
                d.rounded_rectangle([x0+12,ny,x0+238,ny+38], radius=6, fill=fill or "#f3f3f3")
                d.text((x0+26,ny+8), n, font=font(20), fill="#1a1a1a")
                ny += 44
            # content rows
            ry = y0+70
            for i, it in enumerate(items[:9]):
                d.rectangle([x0+266,ry,x1-16,ry+52], outline="#eef1f4", width=2)
                d.rounded_rectangle([x0+278,ry+8,x0+322,ry+44], radius=6, fill="#e8f1fb")
                d.text((x0+290,ry+12), "⛭", font=font(22), fill="#0067c0")
                d.text((x0+336,ry+12), str(it)[:38], font=font(20), fill="#1a1a1a")
                d.text((x1-38,ry+10), "›", font=font(24), fill="#8a919a")
                if (i+1) in steps:
                    draw_step_circle(d, x0+290, ry+78 if ry+78<y1-20 else ry+70, steps.index(i+1)+1)
                ry += 56
        elif utype == "cloud":
            # Cloud console (Azure-like dark top, white content)
            d.rounded_rectangle([x0,y0,x1,y1], radius=10, fill="#ffffff", outline="#c8ced6", width=3)
            d.rounded_rectangle([x0,y0,x1,y0+54], radius=10, fill="#24303f", outline="#24303f", width=3)
            d.text((x0+20,y0+12), "☁  Microsoft Azure" if ui.get("brand","azure")=="azure" else "☁  Cloud Console", font=font(22), fill="#ffffff")
            d.rounded_rectangle([x0+330,y0+10,x1-120,y0+44], radius=6, fill="#ffffff")
            d.text((x0+342,y0+15), "🔍  Search resources, services, and docs…", font=font(18), fill="#7a8694")
            d.ellipse([x1-88,y0+14,x1-56,y0+46], fill="#f38f0d")
            # sidebar
            d.rectangle([x0,y0+54,x0+260,y1], fill="#f5f6f8", outline="#e2e6ea", width=2)
            menu = ["Home","Dashboard","All resources","Virtual machines","Storage accounts","Backup center","Monitoring","Cost management"]
            my = y0+76
            for i, mn in enumerate(menu):
                d.rounded_rectangle([x0+12,my,x0+248,my+40], radius=6, fill="#e8f1fb" if i==1 else "#f5f6f8")
                d.text((x0+26,my+9), mn, font=font(19), fill="#1a1a1a")
                if (i+1) in steps: draw_step_circle(d, x0+230, my+20, steps.index(i+1)+1, r=22)
                my += 46
            # content card
            d.rounded_rectangle([x0+280,y0+80,x1-24,y1-24], radius=8, fill="#ffffff", outline="#dde3e8", width=2)
            d.text((x0+300,y0+100), title, font=font(26), fill="#1a1a1a")
            cy = y0+150
            for it in items[:6]:
                d.rounded_rectangle([x0+300,cy,x1-44,cy+56], radius=6, fill="#f7f9fb", outline="#e2e6ea", width=2)
                d.text((x0+318,cy+14), str(it)[:44], font=font(20), fill="#24303f")
                d.rounded_rectangle([x1-150,cy+10,x1-58,cy+46], radius=6, fill="#e86f0c")
                d.text((x1-138,cy+14), "Create", font=font(18), fill="#ffffff")
                if (i+1) in steps: draw_step_circle(d, x0+330, cy+84 if cy+84<y1-30 else cy+74, steps.index(i+1)+1)
                cy += 64
        else:
            # Generic web/browser walkthrough
            d.rounded_rectangle([x0,y0,x1,y1], radius=10, fill="#ffffff", outline="#c8ced6", width=3)
            d.rounded_rectangle([x0,y0,x1,y0+52], radius=10, fill="#f1f3f5", outline="#d5dbe1", width=3)
            d.ellipse([x0+18,y0+18,x0+34,y0+34], fill="#ff5f57")
            d.ellipse([x0+42,y0+18,x0+58,y0+34], fill="#febc2e")
            d.ellipse([x0+66,y0+18,x0+82,y0+34], fill="#28c840")
            d.rounded_rectangle([x0+100,y0+12,x1-90,y0+42], radius=8, fill="#ffffff", outline="#d5dbe1", width=2)
            d.text((x0+112,y0+18), "🔒  "+(ui.get("url") or "https://portal.example.com"), font=font(18), fill="#5f6b7a")
            d.text((x0+30,y0+70), title, font=font(30), fill="#1a1a1a")
            wy = y0+130
            for i, it in enumerate(items[:8]):
                d.rounded_rectangle([x0+30,wy,x1-40,wy+58], radius=8, fill="#f7f9fb", outline="#e2e6ea", width=2)
                d.text((x0+50,wy+14), str(it)[:48], font=font(21), fill="#24303f")
                if (i+1) in steps: draw_step_circle(d, x1-70, wy+29, steps.index(i+1)+1, r=24)
                wy += 66

    # RENDER MODE: code -> terminal, ui -> UI walkthrough, else concept slide

    for i,s in enumerate(slides):
        code = s.get("code") or []
        ui = s.get("ui")
        img = Image.new("RGB",(W,H),"#061633"); d=ImageDraw.Draw(img)
        d.rectangle([0,0,W,12],fill="#ffd51d")
        d.text((60,70),s.get("heading","Slide"),font=font(54),fill="#ffffff")
        if ui:
            draw_ui_slide(d, s)
            img.save(f"slides/slide_{i:03d}.png")
        elif code:
            # Terminal window
            d.rounded_rectangle([60,150,W-60,H-90],radius=16,fill="#0d1117",outline="#2b3441",width=3)
            # title bar
            d.rounded_rectangle([60,150,W-60,205],radius=16,fill="#161b22",outline="#2b3441",width=3)
            d.ellipse([85,168,101,184],fill="#ff5f57")
            d.ellipse([110,168,126,184],fill="#febc2e")
            d.ellipse([135,168,151,184],fill="#28c840")
            d.text((160,164), s.get("terminal_title") or "bash - lab", font=font(20), fill="#8b949e")
            # code lines with prompt, $ for commands
            y=225
            for ln in code[:12]:
                ln=str(ln)
                if ln.startswith("$ "):
                    d.text((85,y), "$ ", font=font(26), fill="#3fb950")
                    d.text((140,y), ln[2:], font=font(26), fill="#e6edf3")
                elif ln.startswith("#"):
                    d.text((85,y), ln, font=font(24), fill="#8b949e")
                elif ln.startswith("//"):
                    d.text((85,y), ln, font=font(24), fill="#8b949e")
                else:
                    d.text((85,y), ln, font=font(26), fill="#79c0ff")
                y+=40
            d.text((60,H-55),"RCW IT Training - www.rcwittraining.in",font=font(24),fill="#4bd7ff")
            img.save(f"slides/slide_{i:03d}.png")
        else:
            d.text((60,y0:=170),"")
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
        if not text and s.get("code"):
            text="Let's look at the next part of the lab. " + " ".join(str(x).replace("$ ","") for x in s["code"][:8])
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
