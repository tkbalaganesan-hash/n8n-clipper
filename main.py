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

        # 1. Download best quality video under 1080p using yt-dlp
        ydl_opts = {
            'format': 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': input_path,
            'overwrites': True,
            'quiet': True
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([req.video_url])

        # 2. Trim first 59 seconds & crop center to 9:16 vertical ratio (1080x1920)
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

        # 3. Return the processed vertical video file
        return FileResponse(output_path, media_type="video/mp4", filename="short.mp4")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))