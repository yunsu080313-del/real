import os
import torch
import whisper
from flask import Flask, render_template, request

app = Flask(__name__)

# GPU 자동 감지
device = "cuda" if torch.cuda.is_available() else "cpu"
model = whisper.load_model("small", device=device)  # Railway는 small 추천

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload():
    transcription = ""

    if "audio" not in request.files:
        return render_template("index.html", transcription="No file uploaded")

    file = request.files["audio"]

    if file.filename == "":
        return render_template("index.html", transcription="No file selected")

    file_path = "temp_audio.wav"
    file.save(file_path)

    try:
        result = model.transcribe(file_path)
        transcription = result["text"]
    except Exception as e:
        transcription = f"Error: {str(e)}"
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

    return render_template("index.html", transcription=transcription)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
