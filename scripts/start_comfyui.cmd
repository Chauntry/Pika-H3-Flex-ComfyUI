@echo off
setlocal
if "%~1"=="" goto usage
if not exist "%~1\python_embeded\python.exe" goto usage
if not exist "%~1\ComfyUI\main.py" goto usage
if not "%~2"=="" set "MINIMAX_H3_LLAMA_BIN=%~2"
pushd "%~1"
"python_embeded\python.exe" -s "ComfyUI\main.py" --windows-standalone-build --listen 127.0.0.1 --port 8188
set "H3_EXIT=%ERRORLEVEL%"
popd
pause
exit /b %H3_EXIT%
:usage
echo Usage: start_comfyui.cmd "D:\AI\ComfyUI_windows_portable" "D:\AI\llama-bin"
exit /b 1
