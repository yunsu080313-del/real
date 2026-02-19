import os
import torch
import whisper
from flask import Flask, render_template, request

app = Flask(__name__)

device = "cuda" if torch.cuda.is_available() else "cpu"
model = whisper.load_model("small", device=device)

@app.route("/", methods=["GET", "POST"])
def index():
    transcription = ""

    if request.method == "POST":
        if "audio" not in request.files:
            transcription = "No file uploaded"
        else:
            file = request.files["audio"]

            if file.filename == "":
                transcription = "No file selected"
            else:
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
