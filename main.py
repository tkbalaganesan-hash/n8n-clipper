import os
import shutil
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import yt_dlp

app = FastAPI()

SECRET_COOKIES = "/etc/secrets/cookies.txt"
WRITABLE_COOKIES = "/tmp/cookies.txt"


def setup_cookies():
    """Copies read-only Render secret to writable /tmp directory."""
    if os.path.exists(SECRET_COOKIES):
        shutil.copyfile(SECRET_COOKIES, WRITABLE_COOKIES)
        os.chmod(WRITABLE_COOKIES, 0o600)


setup_cookies()


class VideoRequest(BaseModel):
    video_url: str


@app.post("/create-short")
def create_short(request: VideoRequest):
    setup_cookies()

    ydl_opts = {
        # Accept best combined format, or best video+audio, or worst as absolute fallback
        "format": "best/bestvideo+bestaudio/worst",
        "cookiefile": WRITABLE_COOKIES if os.path.exists(WRITABLE_COOKIES) else None,
        "outtmpl": "/tmp/%(id)s.%(ext)s",
        # Emulate clients to bypass YouTube format restrictions on cloud IPs
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "web"],
            }
        },
        "quiet": True,
        "no_warnings": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(request.video_url, download=True)
            return {"status": "success", "video_id": info.get("id")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
