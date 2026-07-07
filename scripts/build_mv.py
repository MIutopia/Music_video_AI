# ============================================================
# 燕青门 MV 合成脚本（40段×5秒 慢放版）
# 每段5s素材 → 慢放到目标时长 → 调色 → 拼接 → 字幕 → 音频
# ============================================================

import os, subprocess

FFMPEG = "ffmpeg"
PROJ_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(PROJ_DIR, "videos", "raw")
CLIP_DIR = os.path.join(PROJ_DIR, "videos", "clips")
OUTPUT_DIR = os.path.join(PROJ_DIR, "output")
AUDIO = os.path.join(PROJ_DIR, "audio", "yanqingmen.wav")
SUBS = os.path.join(PROJ_DIR, "subs", "yanqingmen.srt")

os.makedirs(CLIP_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 古风调色滤镜
GRADE = ("eq=saturation=0.75:contrast=1.08:brightness=-0.02,"
         "colorbalance=rs=0.05:gs=-0.03:bs=-0.08,"
         "vignette=PI/5,unsharp=3:3:0.7")

# ============================================================
# 分镜慢放表（21段，每段含2-3个5秒片段）
# 格式: [段名, 目标时长, [(片段序号, 慢放倍率), ...]]
# 备注: fwd_rev=True 表示正反循环
# ============================================================
SEGMENTS = [
    ("S01", 13, [(1,1.3), (2,1.3)]),
    ("S02", 13, [(3,1.3), (4,1.3)]),
    ("S03", 12, [(5,1.2), (6,1.2)]),
    ("S04", 12, [(7,1.2), (8,1.2)]),
    ("S05", 13, [(9,1.3), (10,1.3)]),
    ("S06", 13, [(11,1.3), (12,1.3)]),
    ("S07", 13, [(13,1.3), (14,1.3)]),
    ("S08", 14, [(15,1.4), (16,1.4)]),
    ("S09", 12, [(17,1.2), (18,1.2)]),
    ("S10", 11, [(19,1.1), (20,1.1)]),
    ("S11", 11, [(21,1.1), (22,1.1)]),
    ("S12", 15, [(23,1.0), (24,1.0), (25,1.0)]),
    ("S13", 8,  [(26, "fwd_rev")]),     # 正反循环
    ("S14", 9,  [(27, "fwd_rev")]),     # 正反循环
    ("S15", 14, [(28,1.4), (29,1.4)]),
    ("S16", 12, [(31,1.2), (32,1.2)]),
    ("S17", 13, [(33,1.3), (34,1.3)]),
    ("S18", 12, [(35,1.2), (36,1.2)]),
    ("S19", 14, [(37,1.4), (38,1.4)]),
    ("S20", 14, [(39,1.4), (40,1.4)]),
    ("S21", 14, [(41,1.4)]),
]

# ============================================================
# 处理所有片段
# ============================================================
clip_idx = 0

for seg_name, target_dur, clips in SEGMENTS:
    seg_out = os.path.join(CLIP_DIR, f"seg_{seg_name}.mp4")
    seg_parts = []

    for clip_num, rate in clips:
        clip_idx += 1
        src = os.path.join(RAW_DIR, f"p{clip_num:02d}.mp4")
        part = os.path.join(CLIP_DIR, f"part_{clip_idx:02d}.mp4")

        if not os.path.exists(src):
            print(f"  [WARN]️ 未找到 p{clip_num:02d}.mp4")
            continue

        if rate == "fwd_rev":
            # 正反循环：5s→正放+倒放≈10s→裁剪到目标时长
            rev_part = os.path.join(CLIP_DIR, f"rev_{clip_idx:02d}.mp4")
            # 调色
            subprocess.run([FFMPEG, "-y", "-i", src,
                "-vf", f"{GRADE},format=yuv420p",
                "-c:v", "libx264", "-crf", "18",
                "-an", "-hide_banner", "-loglevel", "warning",
                part], check=True)
            # reverse + concat = 正放+倒放
            subprocess.run([FFMPEG, "-y", "-i", part, "-i", part,
                "-filter_complex",
                "[0:v]reverse[r];[1:v][r]concat=n=2:v=1:a=0,setpts=PTS",
                "-t", str(target_dur),
                "-c:v", "libx264", "-crf", "18", "-preset", "medium",
                "-an", "-hide_banner", "-loglevel", "warning",
                rev_part], check=True)
            seg_parts.append(rev_part)
        elif rate == 1.0:
            # 原速，直接处理
            subprocess.run([FFMPEG, "-y", "-i", src,
                "-vf", f"{GRADE},format=yuv420p",
                "-c:v", "libx264", "-crf", "18",
                "-an", "-hide_banner", "-loglevel", "warning",
                part], check=True)
            seg_parts.append(part)
        else:
            # 慢放：minterpolate 运动补偿
            new_fps = int(24 * rate)
            subprocess.run([FFMPEG, "-y", "-i", src,
                "-vf",
                f"minterpolate=fps={new_fps}:mi_mode=mci:mc_mode=aobmc,"
                f"{GRADE},format=yuv420p",
                "-c:v", "libx264", "-crf", "18",
                "-an", "-hide_banner", "-loglevel", "warning",
                part], check=True)
            seg_parts.append(part)

    # 拼接该段所有片段
    if len(seg_parts) == 1:
        import shutil
        shutil.copy(seg_parts[0], seg_out)
    else:
        with open(os.path.join(CLIP_DIR, "seg_list.txt"), "w") as f:
            for p in seg_parts:
                f.write(f"file '{p}'\n")
        subprocess.run([FFMPEG, "-y", "-f", "concat", "-safe", "0",
            "-i", os.path.join(CLIP_DIR, "seg_list.txt"),
            "-c:v", "libx264", "-crf", "18", "-preset", "medium",
            "-an", "-hide_banner", "-loglevel", "warning",
            seg_out], check=True)

    print(f"  {seg_name} → {target_dur}s [OK]")

# ============================================================
# 拼接所有段 + 字幕 + 音频
# ============================================================
print("\n[拼接] 合成最终MV...")

with open(os.path.join(CLIP_DIR, "final_list.txt"), "w") as f:
    for seg_name, _, _ in SEGMENTS:
        p = os.path.join(CLIP_DIR, f"seg_{seg_name}.mp4")
        if os.path.exists(p):
            f.write(f"file '{p}'\n")

merged = os.path.join(CLIP_DIR, "merged.mp4")
subprocess.run([FFMPEG, "-y", "-f", "concat", "-safe", "0",
    "-i", os.path.join(CLIP_DIR, "final_list.txt"),
    "-c:v", "libx264", "-crf", "18", "-preset", "medium",
    "-an", "-hide_banner", "-loglevel", "warning",
    merged], check=True)

# 字幕 + 音频
final = os.path.join(OUTPUT_DIR, "yanqingmen_mv_final.mp4")
if os.path.exists(SUBS):
    # Windows路径：先正斜杠再转义冒号，避免破坏转义符
    subs_path = SUBS.replace("\\", "/").replace(":", "\\:")
    subprocess.run([FFMPEG, "-y", "-i", merged, "-i", AUDIO,
        "-vf", f"subtitles='{subs_path}':force_style="
               f"'FontName=STKaiti,FontSize=36,PrimaryColour=&HFFFFFF,"
               f"OutlineColour=&H1A1A2E,Outline=3,Shadow=2,MarginV=50'",
        "-c:v", "libx264", "-crf", "18", "-preset", "medium",
        "-c:a", "aac", "-b:a", "320k",
        "-shortest", "-map", "0:v:0", "-map", "1:a:0",
        "-movflags", "+faststart",
        final, "-hide_banner"], check=True)
else:
    subprocess.run([FFMPEG, "-y", "-i", merged, "-i", AUDIO,
        "-c:v", "libx264", "-crf", "18", "-preset", "medium",
        "-c:a", "aac", "-b:a", "320k",
        "-shortest", "-map", "0:v:0", "-map", "1:a:0",
        "-movflags", "+faststart",
        final, "-hide_banner"], check=True)

size = os.path.getsize(final) / (1024*1024)
print(f"\n{'='*55}")
print(f"[DONE] 燕青门 MV 制作完成！")
print(f"📁 {final}")
print(f"📏 {size:.0f}MB")
print(f"{'='*55}")
