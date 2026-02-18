import os
from flask import Flask, request, render_template, send_from_directory
import openai
import whisper
import ffmpeg

# 환경 변수 설정
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Whisper 모델 로드 (base)
model = whisper.load_model("base")

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("file")
    if not file:
        return {"error": "No file uploaded"}, 400
    
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    # 자막 생성
    result = model.transcribe(filepath, language="Korean")
    srt_path = filepath + ".srt"
    with open(srt_path, "w", encoding="utf-8") as f:
        for seg in result["segments"]:
            start = seg["start"]
            end = seg["end"]
            text = seg["text"].strip()
            f.write(f"{int(start*1000)} --> {int(end*1000)}\n{text}\n\n")

    return {"video": file.filename, "srt": os.path.basename(srt_path)}

@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Railway가 포트 제공
    app.run(host="0.0.0.0", port=port)
