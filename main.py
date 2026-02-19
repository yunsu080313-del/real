import os
import re
import torch
import whisper
from flask import Flask, render_template, request

app = Flask(__name__)

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 디바이스 설정
device = "cuda" if torch.cuda.is_available() else "cpu"

# 모델 (품질 우선)
model = whisper.load_model("medium", device=device)


# -----------------------------
# 자막 후처리 함수
# -----------------------------

def clean_text(text):
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"(어+|음+|그+)\s*", "", text)
    return text.strip()


def split_long_text(text, max_length=35):
    words = text.split()
    lines = []
    current = ""

    for word in words:
        if len(current) + len(word) + 1 <= max_length:
            current += " " + word
        else:
            lines.append(current.strip())
            current = word

    if current:
        lines.append(current.strip())

    return "\n".join(lines)


# -----------------------------
# WebVTT 생성
# -----------------------------

def format_timestamp(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02}:{minutes:02}:{secs:06.3f}"


def create_vtt(segments, output_path):
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("WEBVTT\n\n")

        for segment in segments:
            start = format_timestamp(segment["start"])
            end = format_timestamp(segment["end"])

            text = clean_text(segment["text"])
            text = split_long_text(text)

            if text:
                f.write(f"{start} --> {end}\n")
                f.write(f"{text}\n\n")


# -----------------------------
# 라우팅
# -----------------------------

@app.route("/", methods=["GET", "POST"])
def index():
    video_path = None
    subtitle_path = None

    if request.method == "POST":
        file = request.files.get("audio")

        if file and file.filename != "":
            filename = file.filename
            save_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(save_path)

            # 🔥 Whisper 고품질 설정
            result = model.transcribe(
                save_path,
                language="ko",
                task="transcribe",
                temperature=0.0,
                beam_size=5,
                best_of=5,
                fp16=False
            )

            segments = result["segments"]

            # VTT 생성
            base_name = filename.rsplit(".", 1)[0]
            vtt_filename = base_name + ".vtt"
            vtt_path = os.path.join(UPLOAD_FOLDER, vtt_filename)

            create_vtt(segments, vtt_path)

            video_path = f"/static/uploads/{filename}"
            subtitle_path = f"/static/uploads/{vtt_filename}"

    return render_template(
        "index.html",
        video_path=video_path,
        subtitle_path=subtitle_path
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
