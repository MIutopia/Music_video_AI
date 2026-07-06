# ============================================================
# 燕青门 MV 合成脚本（TeleStudio 54段版）
# 54段×5秒 → 拼接 → 字幕 → 音频（自动裁剪到262秒）
# ============================================================

import os, subprocess, glob

FFMPEG = "ffmpeg"
PROJ_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(PROJ_DIR, "videos", "raw")
CLIP_DIR = os.path.join(PROJ_DIR, "videos", "clips")
OUTPUT_DIR = os.path.join(PROJ_DIR, "output")
AUDIO = os.path.join(PROJ_DIR, "audio", "yanqingmen.wav")
SUBS = os.path.join(PROJ_DIR, "subs", "yanqingmen.srt")

os.makedirs(CLIP_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 54段 × 5秒 = 270秒，音频262秒，-shortest自动裁剪末尾
TOTAL_SEGMENTS = 54

# 古风调色滤镜
GRADE = (
    "eq=saturation=0.75:contrast=1.08:brightness=-0.02,"
    "colorbalance=rs=0.05:gs=-0.03:bs=-0.08,"
    "vignette=PI/5,unsharp=3:3:0.7"
)

# 批量标准化所有 5 秒片段
print(f"📁 处理 {TOTAL_SEGMENTS} 段，每段 5 秒...")

for i in range(1, TOTAL_SEGMENTS + 1):
    num = f"{i:02d}"
    src = os.path.join(RAW_DIR, f"p{num}.mp4")
    out = os.path.join(CLIP_DIR, f"graded_{num}.mp4")

    if not os.path.exists(src):
        print(f"  ⚠️ 未找到 p{num}.mp4")
        continue

    subprocess.run([
        FFMPEG, "-y", "-i", src,
        "-vf", f"{GRADE},scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,format=yuv420p",
        "-t", "5",
        "-c:v", "libx264", "-crf", "18", "-preset", "medium",
        "-an", "-hide_banner", "-loglevel", "warning",
        out
    ])
    print(f"  [{num}/{TOTAL_SEGMENTS}] ✅")

# ============================================================
# 拼接 + 字幕 + 音频
# ============================================================
print("\n[拼接] 合并所有片段...")

list_file = os.path.join(CLIP_DIR, "concat.txt")
with open(list_file, "w") as f:
    for i in range(1, TOTAL_SEGMENTS + 1):
        p = os.path.join(CLIP_DIR, f"graded_{i:02d}.mp4")
        if os.path.exists(p):
            f.write(f"file '{p}'\n")

merged = os.path.join(CLIP_DIR, "merged.mp4")
subprocess.run([
    FFMPEG, "-y", "-f", "concat", "-safe", "0",
    "-i", list_file,
    "-c:v", "libx264", "-crf", "18", "-preset", "medium",
    "-an", "-hide_banner", "-loglevel", "warning",
    merged
], check=True)

print("  拼接完成")

# 字幕 + 音频
final = os.path.join(OUTPUT_DIR, "yanqingmen_mv_final.mp4")

if os.path.exists(SUBS) and os.path.exists(AUDIO):
    cmd = [
        FFMPEG, "-y",
        "-i", merged, "-i", AUDIO,
        "-vf",
        f"subtitles='{SUBS}':force_style="
        f"'FontName=STKaiti,FontSize=36,PrimaryColour=&HFFFFFF,"
        f"OutlineColour=&H1A1A2E,Outline=3,Shadow=2,MarginV=50'",
        "-c:v", "libx264", "-crf", "18", "-preset", "medium",
        "-c:a", "aac", "-b:a", "320k",
        "-shortest", "-map", "0:v:0", "-map", "1:a:0",
        "-movflags", "+faststart",
        final, "-hide_banner"
    ]
else:
    print("⚠️ 缺少字幕或音频文件")
    exit(1)

subprocess.run(cmd, check=True)

size = os.path.getsize(final) / (1024*1024)
print(f"\n{'='*55}")
print(f"🎉 燕青门 MV 制作完成！")
print(f"📁 {final}")
print(f"📏 {size:.0f}MB")
print(f"{'='*55}")
