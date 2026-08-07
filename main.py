import os
import subprocess
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import yt_dlp

app = FastAPI()

class VideoRequest(BaseModel):
    video_url: str

@app.get("/")
def health_check():
    return {"status": "ok", "message": "Video Clipper API is running"}

@app.post("/create-short")
def create_short(req: VideoRequest):
    try:
        output_dir = "/tmp/downloads"
        os.makedirs(output_dir, exist_ok=True)
        input_path = os.path.join(output_dir, "raw_input.mp4")
        output_path = os.path.join(output_dir, "short_output.mp4")

        # Clean up old files if they exist
        for f in [input_path, output_path]:
            if os.path.exists(f):
                os.remove(f)

        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'outtmpl': input_path,
            'overwrites': True,
            'quiet': False,
            'extractor_args': {
                'youtube': {
                    'player_client': ['mweb', 'android', 'ios']
                }
            }
        }

        # Check for Render secret cookie file
        secret_cookie_path = "/etc/secrets/cookies.txt"
        if os.path.exists(secret_cookie_path):
            ydl_opts['cookiefile'] = secret_cookie_path
            ydl_opts['cookiefile_read_only'] = True  # Prevents [Errno 30] read-only filesystem crash

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([req.video_url])

        if not os.path.exists(input_path):
            raise Exception("Failed to download video file.")

        # Trim first 59 seconds & crop center to 9:16 vertical ratio (1080x1920)
        ffmpeg_cmd = [
            'ffmpeg', '-y',
            '-i', input_path,
            '-ss', '00:00:00',
            '-t', '00:00:59',
            '-vf', 'crop=ih*(9/16):ih',
            '-c:v', 'libx264',
            '-preset', 'ultrafast',
            '-crf', '28',
            '-c:a', 'aac',
            output_path
        ]
        subprocess.run(ffmpeg_cmd, check=True)

        return FileResponse(output_path, media_type="video/mp4", filename="short.mp4")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
