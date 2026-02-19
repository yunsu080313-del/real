import os
import torch
import whisper
from flask import Flask, render_template, request

app = Flask(__name__)

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

device = "cuda" if torch.cuda.is_available() else "cpu"
model = whisper.load_model("small", device=device)

def format_timestamp(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02}:{minutes:02}:{secs:06.3f}".replace('.', ',')

def create_srt(segments, output_path):
    with open(output_path, "w", encoding="utf-8") as f:
        for i, segment in enumerate(segments, start=1):
            start = format_timestamp(segment["start"])
            end = format_timestamp(segment["end"])
            text = segment["text"].strip()

            f.write(f"{i}\n")
            f.write(f"{start} --> {end}\n")
            f.write(f"{text}\n\n")

@app.route("/", methods=["GET", "POST"])
def index():
    video_path = None
    subtitle_path = None

    if request.method == "POST":
        file = request.files["audio"]

        if file and file.filename != "":
            filename = file.filename
            save_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(save_path)

            result = model.transcribe(save_path)
            segments = result["segments"]

            # SRT 생성
            srt_filename = filename.rsplit(".", 1)[0] + ".srt"
            srt_path = os.path.join(UPLOAD_FOLDER, srt_filename)
            create_srt(segments, srt_path)

            video_path = f"/static/uploads/{filename}"
            subtitle_path = f"/static/uploads/{srt_filename}"

    return render_template(
        "index.html",
        video_path=video_path,
        subtitle_path=subtitle_path
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
