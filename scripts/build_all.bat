@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

title 燕青门 MV 合成

echo ╔══════════════════════════════════════════════════════════╗
echo ║    燕青门 MV · 20段音画对应合成                          ║
echo ╚══════════════════════════════════════════════════════════╝
echo.

set "PROJ_DIR=%~dp0.."
set "RAW_DIR=%PROJ_DIR%\videos\raw"
set "CLIP_DIR=%PROJ_DIR%\videos\clips"
set "OUTPUT=%PROJ_DIR%\output\yanqingmen_mv_final.mp4"
set "AUDIO=%PROJ_DIR%\audio\yanqingmen.wav"
set "SUBS=%PROJ_DIR%\subs\yanqingmen.srt"

if not exist "%CLIP_DIR%" mkdir "%CLIP_DIR%"
if not exist "%PROJ_DIR%\output" mkdir "%PROJ_DIR%\output"

REM ============================================================
REM 检查环境
REM ============================================================
where ffmpeg >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 未找到 ffmpeg
    pause & exit /b 1
)
if not exist "%AUDIO%" (
    echo ❌ 缺少音频: %AUDIO%
    pause & exit /b 1
)

REM 统计视频
set "VC=0"
for %%f in ("%RAW_DIR%\*.mp4" "%RAW_DIR%\*.webm") do set /a VC+=1
if %VC% equ 0 (
    echo ❌ 未在 videos\raw\ 中找到视频
    pause & exit /b 1
)
echo ✅ 找到 %VC% 个视频
echo.

REM 获取音频时长
for /f "tokens=*" %%a in ('ffprobe -v error -show_entries format^=duration -of default^=noprint_wrappers^=1:nokey^=1 "%AUDIO%" 2^>nul') do set "AUDIO_DUR=%%a"
echo   歌曲时长: %AUDIO_DUR% 秒
echo.

REM ============================================================
REM Step 1: 标准化视频
REM ============================================================
echo [1/3] 标准化视频为 1920x1080 24fps...

set "IDX=0"
for %%f in ("%RAW_DIR%\*.mp4" "%RAW_DIR%\*.webm") do (
    set /a IDX+=1
    set "NUM=00!IDX!"
    set "NUM=!NUM:~-2!"

    ffmpeg -y -i "%%f" ^
        -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,fps=24,format=yuv420p" ^
        -c:v libx264 -crf 18 -preset medium -an -hide_banner -loglevel warning ^
        "%CLIP_DIR%\clip_!NUM!.mp4"

    for /f "tokens=*" %%d in ('ffprobe -v error -show_entries format^=duration -of default^=noprint_wrappers^=1:nokey^=1 "%CLIP_DIR%\clip_!NUM!.mp4" 2^>nul') do set "D=%%d"
    echo   视频 !NUM! → 标准化完成（!D!秒）
)

echo ✅ 标准化完成
echo.

REM ============================================================
REM Step 2: concat 拼接
REM ============================================================
echo [2/3] 拼接视频...

set "LIST=%TEMP%\mv_list.txt"
if exist "%LIST%" del "%LIST%"

for /L %%i in (1,1,%VC%) do (
    set "NUM=00%%i"
    set "NUM=!NUM:~-2!"
    echo file '%CLIP_DIR%\clip_!NUM!.mp4' >> "%LIST%"
)

ffmpeg -y -f concat -safe 0 -i "%LIST%" ^
    -c:v libx264 -crf 18 -preset medium -an -hide_banner ^
    "%CLIP_DIR%\merged.mp4"

if !errorlevel! neq 0 (
    echo ❌ 拼接失败
    pause & exit /b 1
)

for /f "tokens=*" %%d in ('ffprobe -v error -show_entries format^=duration -of default^=noprint_wrappers^=1:nokey^=1 "%CLIP_DIR%\merged.mp4" 2^>nul') do set "VIDEO_DUR=%%d"

echo ✅ 拼接完成（视频 %VIDEO_DUR% 秒 / 音频 %AUDIO_DUR% 秒）

REM 判断视频是否够长
for /f %%c in ('powershell -Command "$v=[double]%VIDEO_DUR%; $a=[double]%AUDIO_DUR%; if($v -ge $a){Write-Host 0}else{Write-Host 1}"') do set "NEED_LOOP=%%c"
echo.

REM ============================================================
REM Step 3: 字幕 + 音频合成
REM ============================================================
echo [3/3] 字幕 + 音频合成...

if !NEED_LOOP! equ 1 (
    echo   视频比歌曲短，自动循环填满时长
    set "LOOP_FLAG=-stream_loop -1"
) else (
    set "LOOP_FLAG="
)

if exist "%SUBS%" (
    ffmpeg -y !LOOP_FLAG! -i "%CLIP_DIR%\merged.mp4" -i "%AUDIO%" ^
        -vf "subtitles='%SUBS%':force_style='FontName=STKaiti,FontSize=36,PrimaryColour=&HFFFFFF,OutlineColour=&H1A1A2E,Outline=3,Shadow=2,MarginV=50'" ^
        -c:v libx264 -crf 18 -preset medium ^
        -c:a aac -b:a 320k ^
        -shortest -map 0:v:0 -map 1:a:0 ^
        -movflags +faststart ^
        "%OUTPUT%" -hide_banner
) else (
    ffmpeg -y !LOOP_FLAG! -i "%CLIP_DIR%\merged.mp4" -i "%AUDIO%" ^
        -c:v libx264 -crf 18 -preset medium ^
        -c:a aac -b:a 320k ^
        -shortest -map 0:v:0 -map 1:a:0 ^
        -movflags +faststart ^
        "%OUTPUT%" -hide_banner
)

if !errorlevel! equ 0 (
    for /f "tokens=*" %%s in ('ffprobe -v error -show_entries format^=duration -of default^=noprint_wrappers^=1:nokey^=1 "%OUTPUT%" 2^>nul') do set "OUT=%%s"
    echo.
    echo ╔══════════════════════════════════════════════════════════╗
    echo ║          🎉 燕青门 MV 制作完成！                         ║
    echo ╚══════════════════════════════════════════════════════════╝
    echo.
    echo   输出: %OUTPUT%
    echo   时长: %OUT% 秒
    for %%f in ("%OUTPUT%") do echo   大小: %%~zf 字节
) else (
    echo ❌ 合成失败
    pause & exit /b 1
)

pause
