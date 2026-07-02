@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ============================================================
echo  Step 2/3 - 视频拼接 + 转场
echo ============================================================
echo.

set "IN_DIR=%~dp0..\videos\processed"
set "OUT_DIR=%~dp0..\videos"

echo [信息] 扫描标准化后的视频文件...
set "FILE_LIST="
set "COUNT=0"

REM 找所有 mp4 文件，按文件名排序
for /f "tokens=*" %%f in ('dir /b /on "%IN_DIR%\*.mp4" 2^>nul') do (
    set /a COUNT+=1
    set "FILE_LIST=!FILE_LIST! -i "%IN_DIR%\%%f""
    set "NAMES=!NAMES! %%f"
)

if %COUNT% lss 2 (
    echo [错误] 至少需要 2 个视频文件才能拼接
    echo 当前找到: %COUNT% 个
    pause
    exit /b 1
)

echo [信息] 找到 %COUNT% 个视频文件
echo.
echo [执行] 使用 concat 协议拼接（无转场，稳定可靠）...

REM 创建 concat 文件列表
set "LIST_FILE=%TEMP%\concat_list.txt"
if exist "%LIST_FILE%" del "%LIST_FILE%"

for %%f in ("%IN_DIR%\*.mp4") do (
    echo file '%%f' >> "%LIST_FILE%"
)

ffmpeg -y -f concat -safe 0 -i "%LIST_FILE%" ^
    -c:v libx264 -crf 18 -preset medium ^
    -an -hide_banner ^
    "%OUT_DIR%\merged_video.mp4"

if !errorlevel! equ 0 (
    echo ✅ 拼接成功！
    echo 输出: %OUT_DIR%\merged_video.mp4
) else (
    echo ❌ 拼接失败
    echo.
    echo [提示] 如果报错请检查视频分辨率/编码是否一致
    echo 可以尝试手动运行 ffprobe 查看视频信息
)

pause
