import os
import torch
import whisper
from flask import Flask, render_template, request

app = Flask(__name__)

# GPU 자동 감지
device = "cuda" if torch.cuda.is_available() else "cpu"
model = whisper.load_model("medium", device=device)

@app.route("/", methods=["GET", "POST"])
def index():
    transcription = ""
    if request.method == "POST":
        file = request.files["audio"]
        if file:
            file_path = "temp_audio.wav"
            file.save(file_path)

            result = model.transcribe(file_path)
            transcription = result["text"]

            os.remove(file_path)

    return render_template("index.html", transcription=transcription)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
