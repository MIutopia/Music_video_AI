@echo off
chcp 65001 >nul
title 燕青门 MV 一键合成

echo ╔══════════════════════════════════════════════════════════╗
echo ║           燕青门 MV · 一键合成                          ║
echo ╚══════════════════════════════════════════════════════════╝
echo.
echo [检查] 运行环境...

where ffmpeg >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 未找到 ffmpeg！
    echo 请从 https://ffmpeg.org/download.html 下载并添加到 PATH
    pause
    exit /b 1
)
echo ✅ ffmpeg 已就绪
echo.

echo ═══════════════════════════════════════════════════════════
echo  前置条件确认
echo ═══════════════════════════════════════════════════════════
echo.
echo 请确保已完成以下步骤，否则脚本会失败：
echo.
echo   [1] audio\yanqingmen.wav  ← 歌曲音频已放入
echo   [2] videos\raw\*.mp4      ← Kling 视频素材已放入
echo.
choice /m "确认以上准备好，开始合成？"
if errorlevel 2 exit /b

echo.
call "%~dp001_normalize.bat"
if %errorlevel% neq 0 (
    echo ❌ 标准化失败，终止
    pause
    exit /b 1
)

call "%~dp002_merge.bat"
if %errorlevel% neq 0 (
    echo ❌ 拼接失败，终止
    pause
    exit /b 1
)

call "%~dp003_finalize.bat"
if %errorlevel% neq 0 (
    echo ❌ 最终合成失败，终止
    pause
    exit /b 1
)

echo.
echo ╔══════════════════════════════════════════════════════════╗
echo ║          🎉 燕青门 MV 制作完成！                         ║
echo ║          输出文件: output\yanqingmen_mv_final.mp4        ║
echo ╚══════════════════════════════════════════════════════════╝
pause
