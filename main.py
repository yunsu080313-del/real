import os
import re
import torch
import whisper
from flask import Flask, render_template, request
from gtts import gTTS
from googletrans import Translator

app = Flask(__name__)

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

device = "cuda" if torch.cuda.is_available() else "cpu"
model = whisper.load_model("small", device=device)

translator = Translator()


# -----------------------------
# 텍스트 정리
# -----------------------------
def clean_text(text):
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# -----------------------------
# VTT 생성
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

            if text:
                f.write(f"{start} --> {end}\n")
                f.write(f"{text}\n\n")


# -----------------------------
# 번역 함수 (ko → en)
# -----------------------------
def translate_text(text):
    translated = translator.translate(text, src="ko", dest="en")
    return translated.text


# -----------------------------
# 더빙 생성 (영어 음성)
# -----------------------------
def create_dubbing(text, output_path):
    tts = gTTS(text=text, lang="en")
    tts.save(output_path)


# -----------------------------
# 라우팅
# -----------------------------
@app.route("/", methods=["GET", "POST"])
def index():
    video_path = None
    subtitle_path = None
    dubbing_path = None

    if request.method == "POST":
        file = request.files.get("audio")

        if file and file.filename != "":
            filename = file.filename
            save_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(save_path)

            # 1️⃣ STT (한국어)
            result = model.transcribe(
                save_path,
                language="ko",
                temperature=0.0,
                beam_size=5,
                best_of=5,
                fp16=False
            )

            segments = result["segments"]

            # 전체 텍스트 합치기
            full_text_ko = " ".join(
                clean_text(seg["text"]) for seg in segments
            )

            # 2️⃣ 번역 (영어)
            full_text_en = translate_text(full_text_ko)

            # 3️⃣ 자막 생성 (한국어)
            base_name = filename.rsplit(".", 1)[0]
            vtt_filename = base_name + ".vtt"
            vtt_path = os.path.join(UPLOAD_FOLDER, vtt_filename)
            create_vtt(segments, vtt_path)

            # 4️⃣ 영어 더빙 생성
            dubbing_filename = base_name + "_dub_en.mp3"
            dubbing_full_path = os.path.join(UPLOAD_FOLDER, dubbing_filename)
            create_dubbing(full_text_en, dubbing_full_path)

            video_path = f"/static/uploads/{filename}"
            subtitle_path = f"/static/uploads/{vtt_filename}"
            dubbing_path = f"/static/uploads/{dubbing_filename}"

    return render_template(
        "index.html",
        video_path=video_path,
        subtitle_path=subtitle_path,
        dubbing_path=dubbing_path
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
