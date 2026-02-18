import os
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import whisper
import pyttsx3
import tempfile

# 로컬 테스트용
if os.path.exists(".env"):
    load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

app = FastAPI()

# Railway는 임시 폴더 /tmp 사용 가능
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# Whisper 모델
model = whisper.load_model("base")

# 홈 페이지
@app.get("/", response_class=HTMLResponse)
def home():
    with open("templates/index.html", "r", encoding="utf-8") as f:
        return f.read()

# 파일 업로드 + 자막 + TTS
@app.post("/upload/")
async def upload_video(file: UploadFile = File(...), lang: str = "ko"):
    # 임시 파일 저장
    upload_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(upload_path, "wb") as f:
        f.write(await file.read())

    # Whisper로 자막 생성
    result = model.transcribe(upload_path, language=lang)
    srt_path = f"{upload_path}.srt"
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write(result.get("subtitles", ""))

    # pyttsx3 TTS
    tts_path = f"{upload_path}_tts.mp3"
    tts = pyttsx3.init()
    tts.setProperty('rate', 150)
    tts.save_to_file(" ".join([seg['text'] for seg in result['segments']]), tts_path)
    tts.runAndWait()

    return {
        "video": upload_path,
        "srt": srt_path,
        "tts": tts_path
    }
