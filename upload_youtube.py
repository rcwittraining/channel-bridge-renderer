#!/usr/bin/env python3
"""
RCW Renderer -> YouTube auto-upload.
Reads output.mp4 + video_script.json (title/desc/tags) + credentials from env,
uploads to the channel, optionally adds to a playlist, prints VIDEO_URL.
After success the workflow skips/cleans artifacts (nothing persists).
"""
import os, sys, json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

def main():
    video = "output.mp4"
    if not os.path.exists(video):
        sys.exit("output.mp4 not found — render step failed")

    # credentials from env (set by the workflow from dispatch inputs / secrets)
    cid = os.environ.get("YT_CLIENT_ID", "").strip()
    sec = os.environ.get("YT_CLIENT_SECRET", "").strip()
    ref = os.environ.get("YT_REFRESH_TOKEN", "").strip()
    if not (cid and sec and ref):
        print("SKIP_UPLOAD=missing youtube credentials (set YT_CLIENT_ID/SECRET/REFRESH_TOKEN)")
        return

    script = json.load(open("video_script.json", encoding="utf-8"))
    title = os.environ.get("YT_TITLE", "").strip() or script.get("title", "RCW IT Training Lab")
    desc = os.environ.get("YT_DESC", "").strip() or script.get("description", "")
    if not desc:
        desc = "Hands-on lab exercise from RCW IT Training.\n\nPractice free: www.rcwittraining.in"
    tags = json.loads(os.environ.get("YT_TAGS", "[]") or "[]")
    if not tags:
        tags = script.get("tags", []) or ["RCW IT Training", "IT Lab"]
    privacy = os.environ.get("YT_PRIVACY", "unlisted").strip()
    playlist = os.environ.get("YT_PLAYLIST", "").strip()

    creds = Credentials.from_authorized_user_info({
        "client_id": cid,
        "client_secret": sec,
        "refresh_token": ref,
        "token_uri": "https://oauth2.googleapis.com/token",
        "scopes": [
            "https://www.googleapis.com/auth/youtube.upload",
            "https://www.googleapis.com/auth/youtube",
        ],
    })
    yt = build("youtube", "v3", credentials=creds)

    body = {
        "snippet": {"title": title, "description": desc, "tags": tags, "categoryId": "27"},
        "status": {"privacyStatus": privacy, "selfDeclaredMadeForKids": False},
    }
    media = MediaFileUpload(video, chunksize=8 * 1024 * 1024, resumable=True)
    req = yt.videos().insert(part="snippet,status", body=body, media_body=media)
    resp = None
    print("UPLOADING=" + title, flush=True)
    while resp is None:
        status, resp = req.next_chunk()
        if status:
            print(f"PROGRESS={int(status.progress()*100)}%", flush=True)
    vid = resp["id"]
    print(f"VIDEO_URL=https://youtu.be/{vid}", flush=True)

    if playlist:
        try:
            yt.playlistItems().insert(part="snippet", body={"snippet": {
                "playlistId": playlist,
                "resourceId": {"kind": "youtube#video", "videoId": vid},
            }}).execute()
            print(f"PLAYLIST_ADDED={playlist}", flush=True)
        except Exception as e:
            print(f"PLAYLIST_WARN={e}", flush=True)

    print("UPLOAD_OK=1", flush=True)

if __name__ == "__main__":
    main()
