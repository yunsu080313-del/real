import os
import re
import torch
import whisper
import subprocess
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
# 유틸
# -----------------------------
def clean_text(text):
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def format_timestamp(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02}:{minutes:02}:{secs:06.3f}"


def change_speed(sound, speed=1.0):
    sound_with_altered_frame_rate = sound._spawn(
        sound.raw_data,
        overrides={"frame_rate": int(sound.frame_rate * speed)}
    )
    return sound_with_altered_frame_rate.set_frame_rate(sound.frame_rate)


# -----------------------------
# 자막 생성
# -----------------------------
def create_vtt(segments, output_path, target_lang):
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("WEBVTT\n\n")

        for seg in segments:
            start = format_timestamp(seg["start"])
            end = format_timestamp(seg["end"])
            text = clean_text(seg["text"])

            if target_lang != "ko":
                text = translator.translate(text, src="ko", dest=target_lang).text

            if text:
                f.write(f"{start} --> {end}\n{text}\n\n")


# -----------------------------
# 싱크 더빙 생성 + 속도 조절
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

        text_translated = translator.translate(
            text_ko,
            src="ko",
            dest=target_lang
        ).text

        temp_file = "temp_segment.mp3"
        tts = gTTS(text=text_translated, lang=target_lang)
        tts.save(temp_file)

        segment_audio = AudioSegment.from_mp3(temp_file)
        os.remove(temp_file)

        # 🔥 속도 자동 조절
        actual_length = len(segment_audio)

        if actual_length > 0:
            speed_ratio = actual_length / duration_ms
            segment_audio = change_speed(segment_audio, speed_ratio)

        # 길이 정밀 보정
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

    subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


# -----------------------------
# 라우팅
# -----------------------------
@app.route("/", methods=["GET", "POST"])
def index():
    video_path = None
    subtitle_path = None

    if request.method == "POST":
        file = request.files.get("audio")
        action = request.form.get("action")
        subtitle_lang = request.form.get("subtitle_lang")
        dubbing_lang = request.form.get("dubbing_lang")

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

            if action == "subtitle":
                vtt_filename = base_name + f"_{subtitle_lang}.vtt"
                vtt_path = os.path.join(UPLOAD_FOLDER, vtt_filename)
                create_vtt(segments, vtt_path, subtitle_lang)
                subtitle_path = f"/static/uploads/{vtt_filename}"
                video_path = f"/static/uploads/{filename}"

            if action == "dubbing":
                dubbing_filename = base_name + "_dub.mp3"
                dubbing_path_full = os.path.join(UPLOAD_FOLDER, dubbing_filename)

                create_synced_dubbing(
                    segments,
                    dubbing_path_full,
                    dubbing_lang
                )

                dubbed_video_filename = base_name + "_dubbed.mp4"
                dubbed_video_full = os.path.join(UPLOAD_FOLDER, dubbed_video_filename)

                merge_video_with_dubbing(
                    save_path,
                    dubbing_path_full,
                    dubbed_video_full
                )

                video_path = f"/static/uploads/{dubbed_video_filename}"

    return render_template(
        "index.html",
        video_path=video_path,
        subtitle_path=subtitle_path
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
