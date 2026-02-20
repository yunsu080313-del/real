<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>DUBBY - AI 자막 & 더빙</title>
<script src="https://cdn.tailwindcss.com"></script>

<style>
body {
    font-family: -apple-system, BlinkMacSystemFont, sans-serif;
    background-color: #f8fafc;
    color: #1e293b;
}
.glass-card {
    background: rgba(255,255,255,0.9);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(226,232,240,0.8);
}
.loading-bar {
    height: 20px;
    width: 0%;
    background-color: #3b82f6;
    border-radius: 10px;
    transition: width 0.3s ease;
}
</style>
</head>

<body class="min-h-screen py-6 px-4">

<div class="max-w-5xl mx-auto">

<header class="mb-8">
    <h1 class="text-2xl font-bold">DUBBY</h1>
    <p class="text-sm text-slate-500">자동 자막 생성 및 AI 더빙</p>
</header>

<main class="grid grid-cols-1 md:grid-cols-12 gap-6">

<!-- 왼쪽 패널 -->
<div class="md:col-span-5">
    <div class="glass-card p-6 rounded-2xl shadow-sm space-y-4">

        <input type="file" id="videoFile" accept="video/*,audio/*" class="w-full">

        <select id="language" class="w-full p-3 border rounded-xl">
            <option value="ko">한국어</option>
            <option value="en">English</option>
            <option value="ja">日本語</option>
            <option value="zh-cn">中文</option>
        </select>

        <button id="subtitleBtn"
                class="w-full bg-blue-600 text-white p-3 rounded-xl">
            자막 생성
        </button>

        <button id="dubbingBtn"
                class="w-full bg-slate-900 text-white p-3 rounded-xl">
            더빙 생성
        </button>

        <!-- 진행률 -->
        <div>
            <div class="w-full bg-slate-200 rounded-full h-5">
                <div id="progressBar" class="loading-bar"></div>
            </div>
            <p class="text-right text-xs mt-1" id="progressText">0%</p>
        </div>

    </div>
</div>

<!-- 오른쪽 결과 영역 -->
<div class="md:col-span-7">
    <div class="glass-card min-h-[400px] p-4 rounded-2xl flex flex-col items-center justify-center">

        <video id="resultVideo" controls class="hidden w-full rounded-lg mb-4"></video>

        <a id="subtitleLink"
           href="#"
           target="_blank"
           class="hidden text-blue-600 underline">
           자막 다운로드
        </a>

    </div>
</div>

</main>
</div>

<script>

// -----------------------------
// DOM 요소
// -----------------------------

const subtitleBtn = document.getElementById("subtitleBtn");
const dubbingBtn = document.getElementById("dubbingBtn");
const videoInput = document.getElementById("videoFile");
const languageSelect = document.getElementById("language");

const progressBar = document.getElementById("progressBar");
const progressText = document.getElementById("progressText");
const resultVideo = document.getElementById("resultVideo");
const subtitleLink = document.getElementById("subtitleLink");

// -----------------------------
// 진행률 표시
// -----------------------------

function setProgress(percent){
    progressBar.style.width = percent + "%";
    progressText.textContent = percent + "%";
}

// -----------------------------
// 파일 검사
// -----------------------------

function validateFile(){
    const file = videoInput.files[0];
    if(!file){
        alert("파일을 선택하세요.");
        return null;
    }
    return file;
}

// -----------------------------
// 서버 요청 공통 함수
// -----------------------------

async function sendRequest(action){

    const file = validateFile();
    if(!file) return;

    setProgress(10);

    const formData = new FormData();
    formData.append("audio", file); // Flask에서 audio로 받음
    formData.append("action", action);

    if(action === "subtitle"){
        formData.append("subtitle_lang", languageSelect.value);
    }

    if(action === "dubbing"){
        formData.append("dubbing_lang", languageSelect.value);
    }

    try{
        const response = await fetch("/process", {
            method: "POST",
            body: formData
        });

        setProgress(70);

        const result = await response.json();

        if(result.error){
            alert(result.error);
            setProgress(0);
            return;
        }

        if(result.video_path){
            resultVideo.src = result.video_path;
            resultVideo.classList.remove("hidden");
        }

        if(result.subtitle_path){
            subtitleLink.href = result.subtitle_path;
            subtitleLink.classList.remove("hidden");
        }

        setProgress(100);

    }catch(error){
        console.error(error);
        alert("서버 통신 오류");
        setProgress(0);
    }
}

// -----------------------------
// 버튼 이벤트 연결
// -----------------------------

subtitleBtn.addEventListener("click", () => {
    sendRequest("subtitle");
});

dubbingBtn.addEventListener("click", () => {
    sendRequest("dubbing");
});

</script>

</body>
</html>
