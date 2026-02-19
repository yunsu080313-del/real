import os
import torch
import whisper
from flask import Flask, render_template, request

app = Flask(__name__)

# 업로드 폴더 설정
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Whisper 모델 로드
device = "cuda" if torch.cuda.is_available() else "cpu"
model = whisper.load_model("small", device=device)

@app.route("/", methods=["GET", "POST"])
def index():
    transcription = ""
    video_path = None

    if request.method == "POST":
        if "audio" not in request.files:
            transcription = "No file uploaded"
        else:
            file = request.files["audio"]

            if file.filename == "":
                transcription = "No file selected"
            else:
                # 파일 저장
                filename = file.filename
                save_path = os.path.join(UPLOAD_FOLDER, filename)
                file.save(save_path)

                try:
                    # Whisper로 변환
                    result = model.transcribe(save_path)
                    transcription = result["text"]

                    # 영상 경로 (HTML에서 재생용)
                    video_path = f"/static/uploads/{filename}"

                except Exception as e:
                    transcription = f"Error: {str(e)}"

    return render_template(
        "index.html",
        transcription=transcription,
        video_path=video_path
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
