# ============================================================
# 燕青门 MV 合成脚本
# 支持：方案1（图片+Ken Burns）和方案2（Wan2.2视频+慢放）
# 自动检测 videos/raw/ 中的文件类型
# ============================================================

import os, subprocess, time, glob, math

FFMPEG = "ffmpeg"
PROJ_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(PROJ_DIR, "videos", "raw")
CLIP_DIR = os.path.join(PROJ_DIR, "videos", "clips")
OUTPUT_DIR = os.path.join(PROJ_DIR, "output")
AUDIO = os.path.join(PROJ_DIR, "audio", "yanqingmen.wav")
SUBS = os.path.join(PROJ_DIR, "subs", "yanqingmen.srt")

os.makedirs(CLIP_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ============================================================
# 分段时间表（每段目标时长 + 标识）
# ============================================================
SEGMENTS = [
    ("S01", 13), ("S02", 13),   # 前奏
    ("S03", 12), ("S04", 12), ("S05", 12),  # 女声 Verse1
    ("S06", 13), ("S07", 10), ("S08", 13),  # 男声 Verse2
    ("S09", 9), ("S10", 11), ("S11", 11),   # 副歌 Chorus1
    ("S12", 15),    # 间奏
    ("S13", 12), ("S14", 12),   # 女声 Verse3
    ("S15", 14),    # 男声 Verse4
    ("S16", 9), ("S17", 11), ("S18", 11),   # 副歌 Chorus2
    ("S19", 14),    # 桥段
    ("S20", 14), ("S21", 14),   # 尾声
]
assert sum(s[1] for s in SEGMENTS) == 262, f"总时长{sum(s[1] for s in SEGMENTS)}≠262"

# ============================================================
# 检测素材类型（图片还是视频）
# ============================================================
def detect_source_type():
    """检测 raw 目录里是 pXX.png（方案1）还是 vXX.mp4（方案2）"""
    pngs = glob.glob(os.path.join(RAW_DIR, "p*.png"))
    mp4s = glob.glob(os.path.join(RAW_DIR, "v*.mp4"))
    if pngs:
        return "image", "p{:02d}"
    elif mp4s:
        return "video", "v{:02d}"
    return None, None

src_type, src_pattern = detect_source_type()
if not src_type:
    print("❌ 未在 videos/raw/ 中找到 p*.png 或 v*.mp4")
    exit(1)
print(f"📁 检测到素材类型: {src_type}")

# ============================================================
# 处理每个片段
# ============================================================
grade_filter = (
    "eq=saturation=0.75:contrast=1.08:brightness=-0.02,"
    "colorbalance=rs=0.05:gs=-0.03:bs=-0.08,"
    "vignette=PI/5,unsharp=3:3:0.7"
)

for i, (name, target_dur) in enumerate(SEGMENTS, 1):
    num = f"{i:02d}"
    src_name = src_pattern.format(i)
    src_path = os.path.join(RAW_DIR, f"{src_name}.{src_type}")
    out_path = os.path.join(CLIP_DIR, f"graded_{num}.mp4")

    if not os.path.exists(src_path):
        # 尝试其他扩展名
        for ext in ["png", "jpg", "mp4", "webm"]:
            alt = os.path.join(RAW_DIR, f"{src_name}.{ext}")
            if os.path.exists(alt):
                src_path = alt
                break

    if not os.path.exists(src_path):
        print(f"  ⚠️ 未找到 {src_name}, 跳过")
        continue

    print(f"[{num}/{len(SEGMENTS)}] {name} → {target_dur}s")

    if src_type == "image":
        # ======== 方案1: 图片 → Ken Burns ========
        zoom_speed = 0.0012 * (10 / target_dur)  # 根据时长调整速度
        cmd = [
            FFMPEG, "-y", "-loop", "1", "-i", src_path,
            "-vf",
            f"scale=3840:2160:force_original_aspect_ratio=increase,"
            f"crop=1920:1080,"
            f"zoompan=z='min(zoom+{zoom_speed},1.4)':"
            f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            f"d={target_dur*24}:s=1920x1080:fps=24,"
            f"{grade_filter},format=yuv420p",
            "-t", str(target_dur),
            "-c:v", "libx264", "-crf", "20", "-preset", "medium",
            "-an", "-hide_banner", "-loglevel", "warning",
            out_path
        ]

    else:
        # ======== 方案2: 视频 → minterpolate 慢放 ========
        # 原始5秒，需要慢放到 target_dur 秒
        ratio = target_dur / 5.0
        new_fps = round(24 * ratio)

        cmd = [
            FFMPEG, "-y", "-i", src_path,
            "-vf",
            f"minterpolate=fps={new_fps}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir,"
            f"scale=1920:1080:force_original_aspect_ratio=decrease,"
            f"pad=1920:1080:(ow-iw)/2:(oh-ih)/2,"
            f"{grade_filter},format=yuv420p",
            "-t", str(target_dur),
            "-c:v", "libx264", "-crf", "20", "-preset", "medium",
            "-an", "-hide_banner", "-loglevel", "warning",
            out_path
        ]

    subprocess.run(cmd)
    print(f"    ✅ {target_dur}s")

# ============================================================
# 拼接 + 字幕 + 音频
# ============================================================
print("\n[最终] 拼接所有片段...")

# concat 列表
list_file = os.path.join(CLIP_DIR, "concat.txt")
with open(list_file, "w") as f:
    for i in range(1, len(SEGMENTS)+1):
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

if os.path.exists(SUBS):
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
    cmd = [
        FFMPEG, "-y",
        "-i", merged, "-i", AUDIO,
        "-c:v", "libx264", "-crf", "18", "-preset", "medium",
        "-c:a", "aac", "-b:a", "320k",
        "-shortest", "-map", "0:v:0", "-map", "1:a:0",
        "-movflags", "+faststart",
        final, "-hide_banner"
    ]

subprocess.run(cmd, check=True)

size = os.path.getsize(final) / (1024*1024)
print(f"\n{'='*55}")
print(f"🎉 燕青门 MV 制作完成！")
print(f"📁 {final}")
print(f"📏 {size:.0f}MB")
print(f"{'='*55}")
