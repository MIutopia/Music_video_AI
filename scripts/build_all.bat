@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

title 燕青门 MV 合成（5s慢放版）

echo ╔══════════════════════════════════════════════════════════╗
echo ║    燕青门 MV · 5秒片段自动慢放 + 拼接合成                ║
echo ╚══════════════════════════════════════════════════════════╝
echo.

set "PROJ_DIR=%~dp0.."
set "RAW_DIR=%PROJ_DIR%\videos\raw"
set "CLIP_DIR=%PROJ_DIR%\videos\clips"
set "OUTPUT=%PROJ_DIR%\output\yanqingmen_mv_final.mp4"
set "AUDIO=%PROJ_DIR%\audio\yanqingmen.mp3"
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
for %%f in ("%RAW_DIR%\p*.mp4") do set /a VC+=1
if %VC% equ 0 (
    echo ❌ 未在 videos\raw\ 中找到 p01.mp4 ~ p21.mp4
    pause & exit /b 1
)
echo ✅ 找到 %VC% 个视频片段
echo.

REM ============================================================
REM 定义每段目标时长（秒）
REM ============================================================
set "DUR_01=13"
set "DUR_02=13"
set "DUR_03=12"
set "DUR_04=12"
set "DUR_05=13"
set "DUR_06=13"
set "DUR_07=13"
set "DUR_08=14"
set "DUR_09=12"
set "DUR_10=11"
set "DUR_11=11"
set "DUR_12=15"
set "DUR_13=8"
set "DUR_14=9"
set "DUR_15=14"
set "DUR_16=12"
set "DUR_17=13"
set "DUR_18=12"
set "DUR_19=14"
set "DUR_20=14"
set "DUR_21=14"

REM ============================================================
REM Step 1: 标准化 + 慢放每段视频到目标时长
REM ============================================================
echo [1/3] 标准化 + 慢放视频到目标时长...

for /L %%i in (1,1,21) do (
    set "NUM=00%%i"
    set "NUM=!NUM:~-2!"
    set "TARGET=!DUR_%%i!"

    set "SRC=%RAW_DIR%\p!NUM!.mp4"
    set "DST=%CLIP_DIR%\clip_!NUM!.mp4"

    if exist "!SRC!" (
        REM 获取源视频时长
        for /f "tokens=*" %%d in ('ffprobe -v error -show_entries format^=duration -of default^=noprint_wrappers^=1:nokey^=1 "!SRC!" 2^>nul') do set "SRC_DUR=%%d"

        REM 计算慢放因子 = TARGET / SRC_DUR（用 PowerShell）
        for /f %%f in ('powershell -Command "[math]::Round(!TARGET! / !SRC_DUR!, 4)"') do set "FACTOR=%%f"

        echo   p!NUM! → !TARGET!秒（源 !SRC_DUR!秒，慢放 !FACTOR!x）

        ffmpeg -y -i "!SRC!" ^
            -vf "setpts=!FACTOR!*PTS,scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,fps=24,format=yuv420p" ^
            -t !TARGET! ^
            -c:v libx264 -crf 18 -preset medium -an ^
            -hide_banner -loglevel warning ^
            "!DST!"

        if !errorlevel! neq 0 (
            echo   ❌ p!NUM! 处理失败
        ) else (
            echo   ✅ clip_!NUM!.mp4
        )
    ) else (
        echo   ⚠️  缺少 p!NUM!.mp4，跳过
    )
)

echo.
echo ✅ 慢放处理完成
echo.

REM ============================================================
REM Step 2: concat 拼接
REM ============================================================
echo [2/3] 拼接视频...

set "LIST=%TEMP%\mv_list.txt"
if exist "%LIST%" del "%LIST%"

for /L %%i in (1,1,21) do (
    set "NUM=00%%i"
    set "NUM=!NUM:~-2!"
    if exist "%CLIP_DIR%\clip_!NUM!.mp4" (
        echo file '%CLIP_DIR%\clip_!NUM!.mp4' >> "%LIST%"
    )
)

ffmpeg -y -f concat -safe 0 -i "%LIST%" ^
    -c:v libx264 -crf 18 -preset medium -an -hide_banner ^
    "%CLIP_DIR%\merged.mp4"

if !errorlevel! neq 0 (
    echo ❌ 拼接失败
    pause & exit /b 1
)

for /f "tokens=*" %%d in ('ffprobe -v error -show_entries format^=duration -of default^=noprint_wrappers^=1:nokey^=1 "%CLIP_DIR%\merged.mp4" 2^>nul') do set "VIDEO_DUR=%%d"

for /f "tokens=*" %%d in ('ffprobe -v error -show_entries format^=duration -of default^=noprint_wrappers^=1:nokey^=1 "%AUDIO%" 2^>nul') do set "AUDIO_DUR=%%d"

echo ✅ 拼接完成（视频 %VIDEO_DUR% 秒 / 音频 %AUDIO_DUR% 秒）
echo.

REM ============================================================
REM Step 3: 字幕 + 音频合成
REM ============================================================
echo [3/3] 字幕 + 音频合成...

if exist "%SUBS%" (
    ffmpeg -y -i "%CLIP_DIR%\merged.mp4" -i "%AUDIO%" ^
        -vf "subtitles='%SUBS%':force_style='FontName=STKaiti,FontSize=36,PrimaryColour=&HFFFFFF,OutlineColour=&H1A1A2E,Outline=3,Shadow=2,MarginV=50'" ^
        -c:v libx264 -crf 18 -preset medium ^
        -c:a aac -b:a 320k ^
        -shortest -map 0:v:0 -map 1:a:0 ^
        -movflags +faststart ^
        "%OUTPUT%" -hide_banner
) else (
    ffmpeg -y -i "%CLIP_DIR%\merged.mp4" -i "%AUDIO%" ^
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
