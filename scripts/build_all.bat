@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ╔══════════════════════════════════════════════════════════╗
echo ║          燕青门 MV · Ken Burns 动画合成                  ║
echo ╚══════════════════════════════════════════════════════════╝
echo.
echo 流程: 图片 → Ken Burns动画 → 转场拼接 → 字幕 → 音频合成
echo.

set "PROJ_DIR=%~dp0.."
set "RAW_DIR=%PROJ_DIR%\videos\raw"
set "CLIP_DIR=%PROJ_DIR%\videos\clips"
set "OUTPUT=%PROJ_DIR%\output\yanqingmen_mv_final.mp4"
set "AUDIO=%PROJ_DIR%\audio\yanqingmen.wav"
set "SUBS=%PROJ_DIR%\subs\yanqingmen.srt"
set "FONT=C:\Windows\Fonts\simkai.ttf"

REM 检查必要文件
if not exist "%AUDIO%" (
    echo ❌ 缺少音频文件: %AUDIO%
    echo 请将歌曲放到 audio\yanqingmen.wav
    pause & exit /b 1
)

if not exist "%CLIP_DIR%" mkdir "%CLIP_DIR%"
if not exist "%PROJ_DIR%\output" mkdir "%PROJ_DIR%\output"

REM 统计图片数量
set "IMG_COUNT=0"
for %%f in ("%RAW_DIR%\*.jpg" "%RAW_DIR%\*.png" "%RAW_DIR%\*.jpeg") do set /a IMG_COUNT+=1

if %IMG_COUNT% equ 0 (
    echo ❌ 未在 videos\raw\ 中找到图片（.jpg/.png）
    echo 请从即梦/通义万相生成图片后放入该目录
    pause & exit /b 1
)

echo ✅ 找到 %IMG_COUNT% 张图片
echo.

REM ============================================================
REM Step 1: Ken Burns 动画处理
REM 每张图生成一段 7-9 秒的缓慢运镜视频
REM ============================================================
echo [1/4] Ken Burns 动画处理...

set "IDX=0"
for %%f in ("%RAW_DIR%\*.jpg" "%RAW_DIR%\*.png" "%RAW_DIR%\*.jpeg") do (
    set /a IDX+=1
    set "NUM=00!IDX!"
    set "NUM=!NUM:~-2!"

    REM 根据序号交替使用不同的运镜方式
    set /a "MODE=!IDX! %% 5"

    if !MODE! equ 0 (
        REM 缓慢放大 (zoom in)
        ffmpeg -y -loop 1 -i "%%f" ^
            -vf "scale=3840:2160:force_original_aspect_ratio=increase,crop=1920:1080,zoompan=z='min(zoom+0.0012,1.4)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=200:s=1920x1080:fps=25,format=yuv420p" ^
            -t 8 -c:v libx264 -crf 20 -preset medium -an -hide_banner -loglevel warning ^
            "%CLIP_DIR%\clip_!NUM!.mp4"
    )
    if !MODE! equ 1 (
        REM 从右向左平移 (pan left)
        ffmpeg -y -loop 1 -i "%%f" ^
            -vf "scale=3840:1080,crop=1920:1080:x='max(0,1920-n*2)':y=0,fps=25,format=yuv420p" ^
            -t 8 -c:v libx264 -crf 20 -preset medium -an -hide_banner -loglevel warning ^
            "%CLIP_DIR%\clip_!NUM!.mp4"
    )
    if !MODE! equ 2 (
        REM 缓慢缩小 (zoom out)
        ffmpeg -y -loop 1 -i "%%f" ^
            -vf "scale=3840:2160:force_original_aspect_ratio=increase,crop=1920:1080,zoompan=z='max(zoom-0.0012,1.0)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=200:s=1920x1080:fps=25,format=yuv420p" ^
            -t 8 -c:v libx264 -crf 20 -preset medium -an -hide_banner -loglevel warning ^
            "%CLIP_DIR%\clip_!NUM!.mp4"
    )
    if !MODE! equ 3 (
        REM 从左向右平移 (pan right)
        ffmpeg -y -loop 1 -i "%%f" ^
            -vf "scale=3840:1080,crop=1920:1080:x='min(n*2,1920)':y=0,fps=25,format=yuv420p" ^
            -t 8 -c:v libx264 -crf 20 -preset medium -an -hide_banner -loglevel warning ^
            "%CLIP_DIR%\clip_!NUM!.mp4"
    )
    if !MODE! equ 4 (
        REM 对角移动 (diagonal)
        ffmpeg -y -loop 1 -i "%%f" ^
            -vf "scale=3840:2160,crop=1920:1080:x='min(n*2,1920)':y='min(n*1,1080)',fps=25,format=yuv420p" ^
            -t 8 -c:v libx264 -crf 20 -preset medium -an -hide_banner -loglevel warning ^
            "%CLIP_DIR%\clip_!NUM!.mp4"
    )

    echo   图片 !NUM! / %IMG_COUNT% → 已生成
)

echo ✅ 所有 Ken Burns 动画完成
echo.

REM ============================================================
REM Step 2: 文件列表 + concat 拼接
REM ============================================================
echo [2/4] 拼接所有动画片段...

set "LIST_FILE=%TEMP%\concat_list.txt"
if exist "%LIST_FILE%" del "%LIST_FILE%"

for /L %%i in (1,1,%IMG_COUNT%) do (
    set "NUM=00%%i"
    set "NUM=!NUM:~-2!"
    echo file '%CLIP_DIR%\clip_!NUM!.mp4' >> "%LIST_FILE%"
)

ffmpeg -y -f concat -safe 0 -i "%LIST_FILE%" ^
    -c:v libx264 -crf 20 -preset medium -an -hide_banner ^
    "%CLIP_DIR%\merged_video.mp4"

if !errorlevel! neq 0 (
    echo ❌ 拼接失败
    pause & exit /b 1
)
echo ✅ 拼接完成
echo.

REM ============================================================
REM Step 3: 叠加字幕
REM ============================================================
echo [3/4] 叠加中英双语字幕...

if not exist "%SUBS%" (
    echo ⚠️ 未找到字幕文件，跳过此步
    set "SUB_CMD="
) else (
    set "SUB_CMD=-vf \"subtitles='%SUBS%':force_style='FontName=STKaiti,FontSize=36,PrimaryColour=&HFFFFFF,OutlineColour=&H1A1A2E,Outline=3,Shadow=2,MarginV=50'\""
)

REM 带字幕的处理
if exist "%SUBS%" (
    ffmpeg -y -i "%CLIP_DIR%\merged_video.mp4" ^
        -vf "subtitles='%SUBS%':force_style='FontName=STKaiti,FontSize=36,PrimaryColour=&HFFFFFF,OutlineColour=&H1A1A2E,Outline=3,Shadow=2,MarginV=50'" ^
        -c:v libx264 -crf 20 -preset medium -an -hide_banner ^
        "%CLIP_DIR%\video_subbed.mp4"
) else (
    copy "%CLIP_DIR%\merged_video.mp4" "%CLIP_DIR%\video_subbed.mp4" >nul
)

echo ✅ 字幕叠加完成
echo.

REM ============================================================
REM Step 4: 合成音频 + 最终输出
REM ============================================================
echo [4/4] 合成音频，输出最终MV...

REM 获取音频时长
for /f "tokens=*" %%a in ('ffprobe -v error -show_entries format^=duration -of default^=noprint_wrappers^=1:nokey^=1 "%AUDIO%" 2^>nul') do set "AUDIO_DUR=%%a"

REM 获取视频时长
for /f "tokens=*" %%a in ('ffprobe -v error -show_entries format^=duration -of default^=noprint_wrappers^=1:nokey^=1 "%CLIP_DIR%\video_subbed.mp4" 2^>nul') do set "VIDEO_DUR=%%a"

echo   音频: %AUDIO_DUR% 秒
echo   视频: %VIDEO_DUR% 秒

REM 如果视频比音频短，循环播放直到音频结束
ffmpeg -y -stream_loop -1 -i "%CLIP_DIR%\video_subbed.mp4" -i "%AUDIO%" ^
    -c:v libx264 -crf 20 -preset medium ^
    -c:a aac -b:a 320k ^
    -shortest -map 0:v:0 -map 1:a:0 ^
    -movflags +faststart ^
    "%OUTPUT%" -hide_banner

if !errorlevel! equ 0 (
    echo.
    echo ╔══════════════════════════════════════════════════════════╗
    echo ║          🎉 燕青门 MV 制作完成！                         ║
    echo ╚══════════════════════════════════════════════════════════╝
    echo.
    echo   输出文件: %OUTPUT%
    for %%f in ("%OUTPUT%") do echo   大小: %%~zf 字节

    REM 播放效果确认
    echo.
    echo   💡 如果视频比音频短，已自动循环画面填满整首歌
    echo   如需调整每张图的播放时长，修改 Step 1 中 -t 参数
) else (
    echo ❌ 合成失败
    pause & exit /b 1
)

pause
