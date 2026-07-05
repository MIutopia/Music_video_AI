# ============================================================
# 燕青门 MV 合成脚本（可灵15秒版）
# 21段视频 → 裁剪到目标时长 → 调色 → 拼接 → 字幕 → 音频
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

# 分段时间表（每段目标时长）
SEGMENTS = [
    ("S01", 13), ("S02", 13), ("S03", 12), ("S04", 12), ("S05", 13),
    ("S06", 13), ("S07", 10), ("S08", 13), ("S09", 9), ("S10", 11),
    ("S11", 11), ("S12", 15), ("S13", 8), ("S14", 9), ("S15", 14),
    ("S16", 9), ("S17", 13), ("S18", 11), ("S19", 14), ("S20", 14),
    ("S21", 14),
]
assert sum(s[1] for s in SEGMENTS) == 262

# 古风调色滤镜
GRADE = (
    "eq=saturation=0.75:contrast=1.08:brightness=-0.02,"
    "colorbalance=rs=0.05:gs=-0.03:bs=-0.08,"
    "vignette=PI/5,unsharp=3:3:0.7"
)

# 检测素材类型
src_type = None
for f in sorted(os.listdir(RAW_DIR)):
    if f.startswith("p") and f.endswith(".mp4"):
        src_type = "video"
        break
    elif f.startswith("p") and f.endswith((".png", ".jpg")):
        src_type = "image"
        break

if not src_type:
    print("❌ 未在 videos/raw/ 中找到 p*.mp4 或 p*.png")
    exit(1)

print(f"📁 素材类型: {src_type}")

for i, (name, target_dur) in enumerate(SEGMENTS, 1):
    num = f"{i:02d}"
    out_path = os.path.join(CLIP_DIR, f"graded_{num}.mp4")

    if src_type == "video":
        # 可灵视频：裁剪到目标时长（从开头取）
        src = os.path.join(RAW_DIR, f"p{num}.mp4")
        if not os.path.exists(src):
            # 尝试其他命名模式
            for f in os.listdir(RAW_DIR):
                if f.startswith(f"p{num}") and f.endswith(".mp4"):
                    src = os.path.join(RAW_DIR, f)
                    break
        if not os.path.exists(src):
            print(f"  ⚠️ 未找到 p{num}.mp4")
            continue

        cmd = [
            FFMPEG, "-y", "-i", src,
            "-vf", f"{GRADE},format=yuv420p",
            "-t", str(target_dur),     # 裁剪到目标时长
            "-c:v", "libx264", "-crf", "18", "-preset", "medium",
            "-an", "-hide_banner", "-loglevel", "warning",
            out_path
        ]
    else:
        # 图片：Ken Burns 动画
        src = os.path.join(RAW_DIR, f"p{num}.png")
        if not os.path.exists(src):
            for ext in ["png", "jpg", "jpeg"]:
                alt = os.path.join(RAW_DIR, f"p{num}.{ext}")
                if os.path.exists(alt):
                    src = alt
                    break
        if not os.path.exists(src):
            print(f"  ⚠️ 未找到 p{num}.png")
            continue

        cmd = [
            FFMPEG, "-y", "-loop", "1", "-i", src,
            "-vf",
            f"scale=3840:2160:force_original_aspect_ratio=increase,"
            f"crop=1920:1080,"
            f"zoompan=z='min(zoom+0.0012,1.4)':"
            f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            f"d={target_dur*24}:s=1920x1080:fps=24,"
            f"{GRADE},format=yuv420p",
            "-t", str(target_dur),
            "-c:v", "libx264", "-crf", "20", "-preset", "medium",
            "-an", "-hide_banner", "-loglevel", "warning",
            out_path
        ]

    subprocess.run(cmd)
    print(f"  [{num}/21] {name} → {target_dur}s ✅")

# ============================================================
# 拼接 + 字幕 + 音频
# ============================================================
print("\n[拼接] 合并所有片段...")

list_file = os.path.join(CLIP_DIR, "concat.txt")
with open(list_file, "w") as f:
    for i in range(1, 22):
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
