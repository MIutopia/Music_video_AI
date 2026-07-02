@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ============================================================
echo  Step 1/3 - 视频标准化 + 古风调色
echo ============================================================
echo.

set "RAW_DIR=%~dp0..\videos\raw"
set "OUT_DIR=%~dp0..\videos\processed"

if not exist "%OUT_DIR%" mkdir "%OUT_DIR%"

REM 古风调色滤镜
set "GRADE_FILTER=eq=saturation=0.85:contrast=1.1:brightness=-0.03,colorbalance=rs=-0.05:gs=-0.02:bs=0.05,unsharp=3:3:0.7"

echo [信息] 扫描视频文件...
set "COUNT=0"
for %%f in ("%RAW_DIR%\*.mp4" "%RAW_DIR%\*.webm") do (
    set /a COUNT+=1
    set "INPUT=%%f"
    set "FILENAME=%%~nf"

    echo [处理] !COUNT!. !FILENAME! ...

    ffmpeg -y -i "%%f" ^
        -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,%GRADE_FILTER%,fps=24" ^
        -c:v libx264 -crf 18 -preset medium ^
        -an -hide_banner -loglevel warning ^
        "%OUT_DIR%\!FILENAME!.mp4"

    if !errorlevel! equ 0 (
        echo   ✅ 完成
    ) else (
        echo   ❌ 失败
    )
)

if %COUNT% equ 0 (
    echo [警告] 未在 videos\raw\ 中找到视频文件
    echo 请将从 Kling 下载的视频放入该目录后重新运行
) else (
    echo.
    echo ============================================================
    echo  处理完成！共处理 %COUNT% 个文件
    echo  输出目录: %OUT_DIR%
    echo ============================================================
)

pause
