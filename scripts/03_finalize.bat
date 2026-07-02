@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ============================================================
echo  Step 3/3 - 最终合成（字幕 + 音频）
echo ============================================================
echo.

set "PROJ_DIR=%~dp0.."
set "VIDEO=%PROJ_DIR%\videos\merged_video.mp4"
set "AUDIO=%PROJ_DIR%\audio\yanqingmen.wav"
set "SUBS=%PROJ_DIR%\subs\yanqingmen.srt"
set "OUTPUT=%PROJ_DIR%\output\yanqingmen_mv_final.mp4"
set "FONT=C:\Windows\Fonts\simkai.ttf"

if not exist "%PROJ_DIR%\output" mkdir "%PROJ_DIR%\output"

REM 检查输入文件
set "MISSING=0"
if not exist "%VIDEO%" (
    echo ❌ 缺少视频文件: %VIDEO%
    echo   请先运行 02_merge.bat
    set /a MISSING+=1
)
if not exist "%AUDIO%" (
    echo ❌ 缺少音频文件: %AUDIO%
    echo   请将生成的歌曲放入 audio\ 目录
    set /a MISSING+=1
)
if %MISSING% gtr 0 (
    pause
    exit /b 1
)

echo [信息] 使用楷体字体: %FONT%
if not exist "%FONT%" (
    echo [警告] 未找到楷体字体，使用默认字体
    set "FONT="
)

echo.
echo [1/2] 叠加字幕 + 合成音频...

if defined FONT (
    ffmpeg -y -i "%VIDEO%" -i "%AUDIO%" ^
        -vf "subtitles='%SUBS%':force_style='FontName=STKaiti,FontSize=36,PrimaryColour=&HFFFFFF,OutlineColour=&H1A1A2E,Outline=3,Shadow=2,MarginV=50'" ^
        -c:v libx264 -crf 18 -preset medium ^
        -c:a aac -b:a 320k ^
        -shortest -map 0:v:0 -map 1:a:0 ^
        -movflags +faststart ^
        "%OUTPUT%" -hide_banner
) else (
    ffmpeg -y -i "%VIDEO%" -i "%AUDIO%" ^
        -vf "subtitles='%SUBS%':force_style='FontSize=36,PrimaryColour=&HFFFFFF,OutlineColour=&H1A1A2E,Outline=3,Shadow=2,MarginV=50'" ^
        -c:v libx264 -crf 18 -preset medium ^
        -c:a aac -b:a 320k ^
        -shortest -map 0:v:0 -map 1:a:0 ^
        -movflags +faststart ^
        "%OUTPUT%" -hide_banner
)

if !errorlevel! equ 0 (
    echo.
    echo ✅ 最终合成成功！
    echo.
    echo ============================================================
    echo  输出文件: %OUTPUT%
    echo  播放试试吧！
    echo ============================================================

    REM 显示文件信息
    for %%f in ("%OUTPUT%") do (
        echo  大小: %%~zf 字节
    )
) else (
    echo ❌ 合成失败
    echo   请检查视频和音频文件是否正常
)

pause
