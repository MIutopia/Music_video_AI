@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

title 燕青门 - 音频按分镜切分

echo ╔══════════════════════════════════════════════════════════╗
echo ║    燕青门 · 按歌词段落切分音频（19段）                  ║
echo ╚══════════════════════════════════════════════════════════╝
echo.

set "AUDIO_DIR=%~dp0..\audio"
set "SEG_DIR=%AUDIO_DIR%\segments"
set "INPUT=%AUDIO_DIR%\yanqingmen.wav"

if not exist "%INPUT%" (
    echo ❌ 未找到音频: %INPUT%
    pause & exit /b 1
)
if not exist "%SEG_DIR%" mkdir "%SEG_DIR%"

echo ✅ 音频: %INPUT%
echo.

REM ============================================================
REM 分段时间表（精确到秒）
REM 来源：用户标注的歌词段落 + 较长段落二次拆分
REM ============================================================

REM 前奏 0:00-0:26 — 拆成 2 段
call :split_seg 01  0  13  "前奏·古城远景"
call :split_seg 02  13 26  "前奏·古城门"

REM 女声Verse1 0:26-1:03 — 拆成 3 段
call :split_seg 03  26 38  "女声·茶馆说书"
call :split_seg 04  38 50  "女声·庭院深深"
call :split_seg 05  50 63  "女声·剑痕武医"

REM 男声Verse2 1:03-1:43 — 拆成 3 段
set /a A=1*60+3
set /a B=1*60+16
set /a C=1*60+29
set /a D=1*60+43
call :split_seg 06  !A! !B! "男声·侠客山巅"
call :split_seg 07  !B! !C! "男声·引箭飞花"
call :split_seg 08  !C! !D! "男声·问剑"

REM 副歌Chorus1 1:43-2:17 — 拆成 3 段
set /a E=1*60+43
set /a F=1*60+55
set /a G=2*60+6
set /a H=2*60+17
call :split_seg 09  !E! !F! "副歌·燕青门"
call :split_seg 10  !F! !G! "副歌·家国天下"
call :split_seg 11  !G! !H! "副歌·弹指剑花"

REM 间奏 2:17-2:32 — 1 段
set /a I=2*60+17
set /a J=2*60+32
call :split_seg 12  !I! !J! "间奏·星河"

REM 女声Verse3 2:32-2:49 — 1 段
set /a K=2*60+32
set /a L=2*60+49
call :split_seg 13  !K! !L! "女声·山河潮水"

REM 男声Verse4 2:49-3:03 — 1 段
set /a M=2*60+49
set /a N=3*60+3
call :split_seg 14  !M! !N! "男声·英雄史册"

REM 副歌Chorus2 3:03-3:40 — 拆成 3 段
set /a O=3*60+3
set /a P=3*60+15
set /a Q=3*60+28
set /a R=3*60+40
call :split_seg 15  !O! !P! "副歌·燕青门"
call :split_seg 16  !P! !Q! "副歌·盛世繁华"
call :split_seg 17  !Q! !R! "副歌·白首韶华"

REM 桥段 3:40-3:54 — 1 段
set /a S=3*60+40
set /a T=3*60+54
call :split_seg 18  !S! !T! "桥段·盛世家园"

REM 尾声 3:54-4:22 — 拆成 2 段
set /a U=3*60+54
set /a V=4*60+8
set /a W=4*60+22
call :split_seg 19  !U! !V! "尾声·策马"
call :split_seg 20  !V! !W! "尾声·落日"

echo.
echo ══════════════════════════════════════════════════════════
echo  ✅ 完成！共 20 段音频已切分
echo  输出: %SEG_DIR%
echo ══════════════════════════════════════════════════════════
pause
exit /b

REM ============================================================
REM 切分函数
REM %1=序号 %2=起始秒 %3=结束秒 %4=描述
REM ============================================================
:split_seg
set "NUM=%1"
set "START=%2"
set "END=%3"
set "DESC=%~4"
set /a "DUR=%END%-%START%"

REM 确保序号 2 位数
if "%NUM%" LSS "10" set "NUM=0%NUM%"

ffmpeg -y -i "%INPUT%" -ss %START% -t %DUR% -c copy "%SEG_DIR%\seg_%NUM%.wav" -hide_banner -loglevel warning

for /f "tokens=*" %%d in ('ffprobe -v error -show_entries format^=duration -of default^=noprint_wrappers^=1:nokey^=1 "%SEG_DIR%\seg_%NUM%.wav" 2^>nul') do set "D=%%d"
echo  seg_%NUM%  %START%s-%END%s (%DUR%s)  %DESC%

exit /b
