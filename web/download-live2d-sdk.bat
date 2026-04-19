@echo off
echo Downloading Live2D Cubism 2 SDK...
curl -L "https://fastly.jsdelivr.net/gh/stevenjoezhang/live2d-widget@latest/assets/live2d.min.js" -o "public/live2d.min.js"
if %ERRORLEVEL% EQU 0 (
    echo Live2D SDK downloaded successfully!
) else (
    echo Failed to download. Trying alternative source...
    curl -L "https://cdn.jsdelivr.net/gh/dylanNew/live2d/webgl/Live2D/lib/live2d.min.js" -o "public/live2d.min.js"
)
echo Done!
pause
