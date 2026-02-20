import os
import re
import uuid
import torch
import whisper
import subprocess
from flask import Flask, render_template, request, jsonify
from gtts import gTTS
from googletrans import Translator
from pydub import AudioSegment
from werkzeug.utils import secure_filename

# -----------------------------
# Flask 설정
# -----------------------------
app = Flask(__name__)
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024  # 500MB 제한

# -----------------------------
# Whisper 모델 + Translator
# -----------------------------
device = "cuda" if torch.cuda.is_available() else "cpu"
model = whisper.load_model("medium", device=device)
translator = Translator()

# -----------------------------
# favicon 404 제거
# -----------------------------
@app.route('/favicon.ico')
def favicon():
    return '', 204

# -----------------------------
# 유틸 함수
# -----------------------------
def clean_text(text):
    return re.sub(r"\s+", " ", text).strip()

def format_timestamp(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02}:{minutes:02}:{secs:06.3f}"

def change_speed(sound, speed=1.0):
    altered = sound._spawn(
        sound.raw_data,
        overrides={"frame_rate": int(sound.frame_rate * speed)}
    )
    return altered.set_frame_rate(sound.frame_rate)

# -----------------------------
# VTT 자막 생성
# -----------------------------
def create_vtt(segments, output_path, target_lang):
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("WEBVTT\n\n")
        for seg in segments:
            start = format_timestamp(seg["start"])
            end = format_timestamp(seg["end"])
            text = clean_text(seg["text"])
            if target_lang != "ko" and text:
                try:
                    text = translator.translate(text, src="ko", dest=target_lang).text
                except:
                    pass
            if text:
                f.write(f"{start} --> {end}\n{text}\n\n")

# -----------------------------
# 싱크 더빙 생성
# -----------------------------
def create_synced_dubbing(segments, output_path, target_lang):
    final_audio = AudioSegment.silent(duration=0)
    for seg in segments:
        start_ms = int(seg["start"] * 1000)
        end_ms = int(seg["end"] * 1000)
        duration_ms = end_ms - start_ms
        text_ko = clean_text(seg["text"])
        if not text_ko:
            continue
        translated = text_ko
        if target_lang != "ko":
            try:
                translated = translator.translate(text_ko, src="ko", dest=target_lang).text
            except:
                pass
        temp_file = "temp_segment.mp3"
        gTTS(text=translated, lang=target_lang).save(temp_file)
        segment_audio = AudioSegment.from_mp3(temp_file)
        os.remove(temp_file)

        actual_length = len(segment_audio)
        if actual_length > 0 and duration_ms > 0:
            speed_ratio = actual_length / duration_ms
            segment_audio = change_speed(segment_audio, speed_ratio)
        segment_audio = segment_audio[:duration_ms]
        if len(segment_audio) < duration_ms:
            segment_audio += AudioSegment.silent(duration=duration_ms - len(segment_audio))
        if len(final_audio) < start_ms:
            final_audio += AudioSegment.silent(duration=start_ms - len(final_audio))
        final_audio += segment_audio
    final_audio.export(output_path, format="mp3")

# -----------------------------
# 영상 + 더빙 합성
# -----------------------------
def merge_video_with_dubbing(video_path, dubbing_path, output_path):
    command = [
        "ffmpeg",
        "-y",
        "-i", video_path,
        "-i", dubbing_path,
        "-c:v", "copy",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-shortest",
        output_path
    ]
    process = subprocess.run(command, capture_output=True, text=True)
    if process.returncode != 0:
        print(process.stderr)
        raise RuntimeError("ffmpeg merge failed")

# -----------------------------
# 메인 라우트 (페이지)
# -----------------------------
@app.route("/")
def index():
    return render_template("index.html")

# -----------------------------
# AJAX 처리 라우트
# -----------------------------
@app.route("/process", methods=["POST"])
def process_video():
    file = request.files.get("audio")
    action = request.form.get("action")
    subtitle_lang = request.form.get("subtitle_lang", "ko")
    dubbing_lang = request.form.get("dubbing_lang", "ko")

    if not file:
        return jsonify({"error": "파일 없음"}), 400

    # 안전한 파일명 + 고유 ID
    filename = secure_filename(file.filename)
    unique_name = str(uuid.uuid4()) + "_" + filename
    save_path = os.path.join(UPLOAD_FOLDER, unique_name)
    file.save(save_path)
    base_name = unique_name.rsplit(".", 1)[0]

    # Whisper 음성 인식
    result = model.transcribe(
        save_path,
        language="ko",
        temperature=0.0,
        beam_size=5,
        best_of=5,
        fp16=False
    )
    segments = result["segments"]

    video_path = None
    subtitle_path = None

    if action == "subtitle":
        vtt_filename = base_name + f"_{subtitle_lang}.vtt"
        vtt_full = os.path.join(UPLOAD_FOLDER, vtt_filename)
        create_vtt(segments, vtt_full, subtitle_lang)
        video_path = f"/static/uploads/{unique_name}"
        subtitle_path = f"/static/uploads/{vtt_filename}"

    elif action == "dubbing":
        dubbing_mp3 = os.path.join(UPLOAD_FOLDER, base_name + "_dub.mp3")
        create_synced_dubbing(segments, dubbing_mp3, dubbing_lang)
        dubbed_video = os.path.join(UPLOAD_FOLDER, base_name + "_dubbed.mp4")
        merge_video_with_dubbing(save_path, dubbing_mp3, dubbed_video)
        video_path = f"/static/uploads/{base_name}_dubbed.mp4"

    return jsonify({
        "video_path": video_path,
        "subtitle_path": subtitle_path
    })

# -----------------------------
# 실행
# -----------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
