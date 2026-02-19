from flask import Flask, request, render_template
import whisper

app = Flask(__name__)

# CPU로 모델 로드
model = whisper.load_model("base", device="cpu")

@app.route("/")
def index():
    return "Whisper TTS 서버 실행 중"

@app.route("/transcribe", methods=["POST"])
def transcribe():
    if "file" not in request.files:
        return "No file uploaded", 400
    audio_file = request.files["file"]
    audio_file.save("temp_audio.wav")
    result = model.transcribe("temp_audio.wav")
    return result["text"]

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
