from flask import Flask, request, send_from_directory, render_template, jsonify
import whisper
import os
from googletrans import Translator
from gtts import gTTS

app = Flask(__name__, template_folder="templates")
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Whisper 모델 로드
model = whisper.load_model("base")
translator = Translator()

# 웹페이지
@app.route("/")
def index():
    return render_template("index.html")

# 영상 업로드 + 자막 생성 + 번역 + TTS
@app.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("video")
    target_lang = request.form.get("lang", "en")
    if not file:
        return "No file", 400

    video_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(video_path)

    # Whisper로 한국어 자막 생성
    result = model.transcribe(video_path, language="ko")
    text_ko = result["text"]

    # 선택 언어로 번역
    text_translated = translator.translate(text_ko, dest=target_lang).text

    # SRT 생성
    srt_path = os.path.join(UPLOAD_FOLDER, file.filename.rsplit(".",1)[0] + ".srt")
    with open(srt_path, "w", encoding="utf-8") as f:
        for idx, line in enumerate(text_translated.split(". "), start=1):
            start_time = f"{(idx-1)*5:02}:00.000"
            end_time = f"{idx*5:02}:00.000"
            f.write(f"{idx}\n{start_time} --> {end_time}\n{line.strip()}\n\n")

    # SRT -> VTT 변환
    vtt_path = os.path.join(UPLOAD_FOLDER, file.filename.rsplit(".",1)[0] + ".vtt")
    with open(srt_path, "r", encoding="utf-8") as f_in, open(vtt_path, "w", encoding="utf-8") as f_out:
        f_out.write("WEBVTT\n\n")
        for idx, line in enumerate(f_in, start=1):
            if "-->" in line or line.strip().isdigit():
                f_out.write(line)
            elif line.strip():
                f_out.write(line)

    # TTS 생성
    tts_path = os.path.join(UPLOAD_FOLDER, file.filename.rsplit(".",1)[0] + f"_{target_lang}.mp3")
    tts = gTTS(text=text_translated, lang=target_lang)
    tts.save(tts_path)

    return jsonify({
        "video": f"/uploads/{file.filename}",
        "subtitle": f"/uploads/{file.filename.rsplit('.',1)[0]}.vtt",
        "audio": f"/uploads/{file.filename.rsplit('.',1)[0]}_{target_lang}.mp3"
    })

# 업로드 파일 서빙
@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
