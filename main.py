import os
import re
import torch
import whisper
from flask import Flask, render_template, request
from gtts import gTTS
from googletrans import Translator
from pydub import AudioSegment

app = Flask(__name__)

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

device = "cuda" if torch.cuda.is_available() else "cpu"
model = whisper.load_model("small", device=device)
translator = Translator()


# -----------------------------
# 공통 함수
# -----------------------------
def clean_text(text):
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def format_timestamp(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02}:{minutes:02}:{secs:06.3f}"


# -----------------------------
# 자막 생성
# -----------------------------
def create_vtt(segments, output_path):
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("WEBVTT\n\n")

        for seg in segments:
            start = format_timestamp(seg["start"])
            end = format_timestamp(seg["end"])
            text = clean_text(seg["text"])

            if text:
                f.write(f"{start} --> {end}\n{text}\n\n")


# -----------------------------
# 문장 단위 싱크 더빙 생성
# -----------------------------
def create_synced_dubbing(segments, output_path):
    final_audio = AudioSegment.silent(duration=0)

    for seg in segments:
        start_ms = int(seg["start"] * 1000)
        end_ms = int(seg["end"] * 1000)
        duration_ms = end_ms - start_ms

        text_ko = clean_text(seg["text"])
        if not text_ko:
            continue

        # 번역
        text_en = translator.translate(text_ko, src="ko", dest="en").text

        # TTS 생성
        temp_file = "temp_segment.mp3"
        tts = gTTS(text=text_en, lang="en")
        tts.save(temp_file)

        segment_audio = AudioSegment.from_mp3(temp_file)

        # 길이 맞추기
        if len(segment_audio) > duration_ms:
            segment_audio = segment_audio[:duration_ms]
        else:
            silence_needed = duration_ms - len(segment_audio)
            segment_audio += AudioSegment.silent(duration=silence_needed)

        # 시작 위치까지 무음 추가
        if len(final_audio) < start_ms:
            final_audio += AudioSegment.silent(duration=start_ms - len(final_audio))

        final_audio += segment_audio

        os.remove(temp_file)

    final_audio.export(output_path, format="mp3")


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
        action = request.form.get("action")

        if file and file.filename != "":
            filename = file.filename
            base_name = filename.rsplit(".", 1)[0]
            save_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(save_path)

            result = model.transcribe(
                save_path,
                language="ko",
                temperature=0.0,
                beam_size=5,
                best_of=5,
                fp16=False
            )

            segments = result["segments"]

            # 자막 버튼
            if action == "subtitle":
                vtt_filename = base_name + ".vtt"
                vtt_path = os.path.join(UPLOAD_FOLDER, vtt_filename)
                create_vtt(segments, vtt_path)
                subtitle_path = f"/static/uploads/{vtt_filename}"

            # 더빙 버튼
            if action == "dubbing":
                dubbing_filename = base_name + "_dub_en.mp3"
                dubbing_full_path = os.path.join(UPLOAD_FOLDER, dubbing_filename)
                create_synced_dubbing(segments, dubbing_full_path)
                dubbing_path = f"/static/uploads/{dubbing_filename}"

            video_path = f"/static/uploads/{filename}"

    return render_template(
        "index.html",
        video_path=video_path,
        subtitle_path=subtitle_path,
        dubbing_path=dubbing_path
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
