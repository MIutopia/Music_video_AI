@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

title 燕青门 MV 合成

echo ╔══════════════════════════════════════════════════════════╗
echo ║       燕青门 MV · 图生视频 → 慢放 → 合成                ║
echo ╚══════════════════════════════════════════════════════════╝
echo.

set "PROJ_DIR=%~dp0.."
set "RAW_DIR=%PROJ_DIR%\videos\raw"
set "SLO_DIR=%PROJ_DIR%\videos\slowmo"
set "OUTPUT=%PROJ_DIR%\output\yanqingmen_mv_final.mp4"
set "AUDIO=%PROJ_DIR%\audio\yanqingmen.wav"
set "SUBS=%PROJ_DIR%\subs\yanqingmen.srt"

if not exist "%SLO_DIR%" mkdir "%SLO_DIR%"
if not exist "%PROJ_DIR%\output" mkdir "%PROJ_DIR%\output"

REM ============================================================
REM 检查环境
REM ============================================================
echo [检查] 运行环境...

where ffmpeg >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 未找到 ffmpeg！
    pause & exit /b 1
)
echo ✅ ffmpeg 已就绪

if not exist "%AUDIO%" (
    echo ❌ 缺少音频: %AUDIO%
    pause & exit /b 1
)
echo ✅ 音频已就绪

REM 统计视频数量
set "VIDEO_COUNT=0"
for %%f in ("%RAW_DIR%\*.mp4" "%RAW_DIR%\*.webm") do set /a VIDEO_COUNT+=1
if %VIDEO_COUNT% equ 0 (
    echo ❌ 未在 videos\raw\ 中找到视频
    pause & exit /b 1
)
echo ✅ 找到 %VIDEO_COUNT% 个视频
echo.

REM ============================================================
REM 获取音频时长
REM ============================================================
for /f "tokens=*" %%a in ('ffprobe -v error -show_entries format^=duration -of default^=noprint_wrappers^=1:nokey^=1 "%AUDIO%" 2^>nul') do set "AUDIO_SEC=%%a"
set /a "AUDIO_INT=!AUDIO_SEC:.=!" 2>nul
if not defined AUDIO_SEC (
    echo ⚠️ 无法读取音频时长
    pause & exit /b 1
)
set "AUDIO_SEC=!AUDIO_SEC:,=.!"
echo   音频时长: %AUDIO_SEC% 秒
echo.

REM ============================================================
REM Step 1: 统一分辨率 + 计算慢放参数
REM ============================================================
echo [1/4] 统一视频分辨率...

set "CLIP_DIR=%PROJ_DIR%\videos\clips"
if not exist "%CLIP_DIR%" mkdir "%CLIP_DIR%"

set /a "IDX=0"
for %%f in ("%RAW_DIR%\*.mp4" "%RAW_DIR%\*.webm") do (
    set /a IDX+=1
    set "NUM=0!IDX!"
    set "NUM=!NUM:~-2!"

    REM 获取原始视频时长
    for /f "tokens=*" %%d in ('ffprobe -v error -show_entries format^=duration -of default^=noprint_wrappers^=1:nokey^=1 "%%f" 2^>nul') do set "DUR=%%d"
    set "DUR=!DUR:,=.!"

    REM 统一为 1920x1080 24fps
    ffmpeg -y -i "%%f" ^
        -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,fps=24,format=yuv420p" ^
        -c:v libx264 -crf 18 -preset medium -an -hide_banner -loglevel warning ^
        "%CLIP_DIR%\raw_!NUM!.mp4"

    echo   视频 !NUM! → 标准化完成（原始 !DUR! 秒）
)

echo ✅ 所有视频标准化完成
echo.

REM ============================================================
REM Step 2: minterpolate 智能慢放
REM 自动计算慢放倍率使总时长匹配音频
REM ============================================================
echo [2/4] 计算慢放参数...

REM 计算原始视频总时长
set "TOTAL_RAW=0"
for /L %%i in (1,1,%VIDEO_COUNT%) do (
    set "NUM=0%%i"
    set "NUM=!NUM:~-2!"
    for /f "tokens=*" %%d in ('ffprobe -v error -show_entries format^=duration -of default^=noprint_wrappers^=1:nokey^=1 "%CLIP_DIR%\raw_!NUM!.mp4" 2^>nul') do set "DUR=%%d"
    for /f %%v in ('powershell "!DUR!"') do set "DUR_INT=%%v"
)

REM 用 PowerShell 计算
for /f %%r in ('powershell -Command "$total=0; $vcount=%VIDEO_COUNT%; for($i=1; $i -le $vcount; $i++){ $n=''{0:d2}'' -f $i; $dur=ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 \""%CLIP_DIR%\raw_$n.mp4\"" 2>&1; if($dur -match ''[\d\.]+''){ $total+=[double]$matches[0] } }; $total"') do set "TOTAL_RAW_SEC=%%r"

echo   原始总时长: %TOTAL_RAW_SEC% 秒

REM 计算需要的慢放倍率
REM 需要考虑转场损耗: (视频段数-1) × 1秒转场
set /a "TRANS_TIME=%VIDEO_COUNT% - 1"
for /f %%s in ('powershell -Command "$audio=[double]%AUDIO_SEC%; $total=[double]%TOTAL_RAW_SEC%; $trans=[int]%TRANS_TIME%; $target=$audio - $trans; if($target -le $total) { $target=$total }; $ratio=$target/$total; Write-Host ([math]::Round($ratio,2))"') do set "SLOW_RATIO=%%s"

echo   所需慢放倍率: %SLOW_RATIO%x

REM minterpolate 运动补偿慢放
echo.
echo   正在执行智能慢放（运动补偿插帧）...
echo   每段约需 1-3 分钟，请耐心等待

for /L %%i in (1,1,%VIDEO_COUNT%) do (
    set "NUM=0%%i"
    set "NUM=!NUM:~-2!"

    REM minterpolate: motion compensated interpolation
    REM 设置 fps 为原始fps×倍率，minterpolate自动插帧
    for /f %%f in ('powershell -Command "[math]::Round(24 * %SLOW_RATIO%)"') do set "NEW_FPS=%%f"

    ffmpeg -y -i "%CLIP_DIR%\raw_!NUM!.mp4" ^
        -vf "minterpolate=fps=!NEW_FPS!:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1" ^
        -c:v libx264 -crf 20 -preset medium -an -hide_banner -loglevel warning ^
        "%SLO_DIR%\slow_!NUM!.mp4"

    for /f "tokens=*" %%d in ('ffprobe -v error -show_entries format^=duration -of default^=noprint_wrappers^=1:nokey^=1 "%SLO_DIR%\slow_!NUM!.mp4" 2^>nul') do set "SD=%%d"
    set "SD=!SD:,=.!"
    echo   视频 !NUM! → 慢放完成（!SD! 秒）
)

echo ✅ 所有慢放完成
echo.

REM ============================================================
REM Step 3: xfade 转场拼接
REM ============================================================
echo [3/4] 转场拼接...

REM 逐段获取慢放后的时长，构建 xfade 滤镜
set "FF_CMD=ffmpeg -y"
set "FILTER="
set "PREV="
set "OFFSET=0"
set "FF_CNT=0"

REM 第一轮：收集输入文件
set "INPUTS="
for /L %%i in (1,1,%VIDEO_COUNT%) do (
    set "NUM=0%%i"
    set "NUM=!NUM:~-2!"
    set "INPUTS=!INPUTS! -i \"%SLO_DIR%\slow_!NUM!.mp4\""
)

REM 用 concat 协议拼接（带 crossfade 需要更复杂的处理）
REM 这里用 concat + 后续可手动优化
set "LIST_FILE=%TEMP%\mv_concat.txt"
if exist "%LIST_FILE%" del "%LIST_FILE%"

REM 获取慢放文件列表并按时长排序
for /L %%i in (1,1,%VIDEO_COUNT%) do (
    set "NUM=0%%i"
    set "NUM=!NUM:~-2!"
    echo file '%SLO_DIR%\slow_!NUM!.mp4' >> "%LIST_FILE%"
)

ffmpeg -y -f concat -safe 0 -i "%LIST_FILE%" ^
    -c:v libx264 -crf 18 -preset medium -an -hide_banner ^
    "%CLIP_DIR%\merged_video.mp4"

if !errorlevel! equ 0 (
    set "MERGED_DUR="
    for /f "tokens=*" %%d in ('ffprobe -v error -show_entries format^=duration -of default^=noprint_wrappers^=1:nokey^=1 "%CLIP_DIR%\merged_video.mp4" 2^>nul') do set "MERGED_DUR=%%d"
    echo ✅ 拼接完成（%MERGED_DUR% 秒）
) else (
    echo ❌ 拼接失败
    pause & exit /b 1
)
echo.

REM ============================================================
REM Step 3.5: 检查时长，如果不够则使用 stream_loop
REM ============================================================
echo [检查] 视频时长 vs 音频时长...

for /f "tokens=*" %%d in ('ffprobe -v error -show_entries format^=duration -of default^=noprint_wrappers^=1:nokey^=1 "%CLIP_DIR%\merged_video.mp4" 2^>nul') do set "VIDEO_SEC=%%d"

for /f %%v in ('powershell -Command "$a=[double]%AUDIO_SEC%; $v=[double]%VIDEO_SEC%; if($v -ge $a){Write-Host 'ok'}else{Write-Host 'short'}"') do set "STATUS=%%v"

if "!STATUS!"=="short" (
    echo   视频（%VIDEO_SEC%秒）比音频（%AUDIO_SEC%秒）短
    set "NEED_LOOP=1"
) else (
    echo   视频（%VIDEO_SEC%秒）足够覆盖音频 ✅
    set "NEED_LOOP=0"
)

REM ============================================================
REM Step 4: 字幕 + 音频 + 最终输出
REM ============================================================
echo [4/4] 叠加字幕 + 合成音频...

REM 判断是否有字幕文件
if exist "%SUBS%" (
    set "SUB_OPT=-vf \"subtitles='%SUBS%':force_style='FontName=STKaiti,FontSize=36,PrimaryColour=&HFFFFFF,OutlineColour=&H1A1A2E,Outline=3,Shadow=2,MarginV=50'\""
) else (
    set "SUB_OPT="
    echo   未找到字幕文件，跳过
)

if exist "%SUBS%" (
    if "!NEED_LOOP!"=="1" (
        REM 循环画面填满音频时长
        ffmpeg -y ^
            -stream_loop -1 -i "%CLIP_DIR%\merged_video.mp4" ^
            -i "%AUDIO%" ^
            -vf "subtitles='%SUBS%':force_style='FontName=STKaiti,FontSize=36,PrimaryColour=&HFFFFFF,OutlineColour=&H1A1A2E,Outline=3,Shadow=2,MarginV=50'" ^
            -c:v libx264 -crf 18 -preset medium ^
            -c:a aac -b:a 320k ^
            -shortest -map 0:v:0 -map 1:a:0 ^
            -movflags +faststart ^
            "%OUTPUT%" -hide_banner
    ) else (
        ffmpeg -y ^
            -i "%CLIP_DIR%\merged_video.mp4" ^
            -i "%AUDIO%" ^
            -vf "subtitles='%SUBS%':force_style='FontName=STKaiti,FontSize=36,PrimaryColour=&HFFFFFF,OutlineColour=&H1A1A2E,Outline=3,Shadow=2,MarginV=50'" ^
            -c:v libx264 -crf 18 -preset medium ^
            -c:a aac -b:a 320k ^
            -shortest -map 0:v:0 -map 1:a:0 ^
            -movflags +faststart ^
            "%OUTPUT%" -hide_banner
    )
) else (
    if "!NEED_LOOP!"=="1" (
        ffmpeg -y ^
            -stream_loop -1 -i "%CLIP_DIR%\merged_video.mp4" ^
            -i "%AUDIO%" ^
            -c:v libx264 -crf 18 -preset medium ^
            -c:a aac -b:a 320k ^
            -shortest -map 0:v:0 -map 1:a:0 ^
            -movflags +faststart ^
            "%OUTPUT%" -hide_banner
    ) else (
        ffmpeg -y ^
            -i "%CLIP_DIR%\merged_video.mp4" ^
            -i "%AUDIO%" ^
            -c:v libx264 -crf 18 -preset medium ^
            -c:a aac -b:a 320k ^
            -shortest -map 0:v:0 -map 1:a:0 ^
            -movflags +faststart ^
            "%OUTPUT%" -hide_banner
    )
)

if !errorlevel! equ 0 (
    echo.
    echo ╔══════════════════════════════════════════════════════════╗
    echo ║          🎉 燕青门 MV 制作完成！                         ║
    echo ╚══════════════════════════════════════════════════════════╝
    echo.
    echo   输出: %OUTPUT%
    echo.
    echo   提示：如果用了循环画面，可以调整 minterpolate 的慢放
    echo   倍率来减少循环次数。在脚本中找到 SLOW_RATIO 即可修改。
) else (
    echo ❌ 合成失败
    pause & exit /b 1
)

pause
