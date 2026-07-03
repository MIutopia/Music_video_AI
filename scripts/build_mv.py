# ============================================================
# 燕青门 MV 合成脚本
# 叙事风格：21张古风图 + Ken Burns动画 + 粒子 + 调色 + 字幕
# 使用方法：python build_mv.py
# ============================================================

import os, subprocess, time, glob
import importlib.util

# 尝试加载特效模块
FX_AVAILABLE = False
fx_spec = importlib.util.spec_from_file_location(
    "effects",
    os.path.join(os.path.dirname(__file__), "effects.py")
)
if fx_spec and fx_spec.loader:
    try:
        effects = importlib.util.module_from_spec(fx_spec)
        fx_spec.loader.exec_module(effects)
        FX_AVAILABLE = True
    except:
        pass

# ============================================================
# 配置
# ============================================================
PROJ_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(PROJ_DIR, "videos", "raw")
CLIP_DIR = os.path.join(PROJ_DIR, "videos", "clips")
OUTPUT_DIR = os.path.join(PROJ_DIR, "output")
AUDIO = os.path.join(PROJ_DIR, "audio", "yanqingmen.wav")
SUBS = os.path.join(PROJ_DIR, "subs", "yanqingmen.srt")
FFMPEG = "ffmpeg"  # 或全路径 "E:/GitHub/ffmpeg/bin/ffmpeg.exe"

os.makedirs(CLIP_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ============================================================
# 叙事分段：21张图的时长分配（秒）
# 叙事节奏：前奏慢→叙事平→副歌快→间奏缓→再起→高潮→尾声
# ============================================================
SEGMENTS = [
    # (文件名, 时长, 运镜类型, 粒子类型)
    # 前奏 · 宁静引入
    ("p01", 13, "zoomin", "gold"),     # 古城全景
    ("p02", 13, "panright", "gold"),   # 古城门

    # 女声 Verse1 · 平缓叙事
    ("p03", 12, "panleft", "none"),    # 茶馆说书
    ("p04", 12, "zoomin", "none"),     # 庭院深深
    ("p05", 12, "zoomout", "none"),    # 剑痕武医

    # 男声 Verse2 · 情绪渐强
    ("p06", 13, "zoomout", "gold"),    # 侠客山巅
    ("p07", 13, "zoomin", "petal"),    # 引箭飞花
    ("p08", 13, "panright", "none"),   # 问剑

    # 副歌 Chorus1 · 高潮
    ("p09", 11, "zoomout", "gold"),    # 燕青门
    ("p10", 11, "diagonal", "gold"),   # 家国天下
    ("p11", 11, "zoomin", "petal"),    # 弹指剑花

    # 间奏 · 情绪回落
    ("p12", 15, "zoomout", "gold"),    # 星河

    # 女声 Verse3 · 再起
    ("p13", 12, "panleft", "none"),    # 星河欲转
    ("p14", 12, "zoomin", "none"),     # 潮水千秋

    # 男声 Verse4 · 升华
    ("p15", 14, "zoomout", "gold"),    # 英雄史册

    # 副歌 Chorus2 · 第二次高潮
    ("p16", 11, "zoomin", "gold"),     # 燕青门内
    ("p17", 11, "panright", "gold"),   # 盛世繁华
    ("p18", 11, "zoomout", "petal"),   # 白首韶华

    # 桥段 · 温暖收束
    ("p19", 14, "panleft", "gold"),    # 盛世家园

    # 尾声 · 悠远淡出
    ("p20", 14, "diagonal", "petal"),  # 策马奔腾
    ("p21", 14, "zoomout", "gold"),    # 落日远方
]

total_time = sum(s[1] for s in SEGMENTS)
print(f"🎬 叙事总时长: {total_time}秒（目标262秒）")
assert abs(total_time - 262) < 5, f"时长不匹配: {total_time} != 262"

# ============================================================
# 运镜函数 - 返回 ffmpeg filter
# ============================================================
def make_kenburns_filter(cam_type, duration, fps=24):
    """生成 Ken Burns 滤镜"""
    frames = duration * fps

    if cam_type == "zoomin":
        # 缓慢放大（从 1.0x 到 1.4x）
        return (
            f"scale=3840:2160:force_original_aspect_ratio=increase,"
            f"crop=1920:1080,"
            f"zoompan=z='min(zoom+0.0012,1.4)':"
            f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            f"d={int(frames)}:s=1920x1080:fps={fps},format=yuv420p"
        )
    elif cam_type == "zoomout":
        # 缓慢缩小（从 1.4x 到 1.0x）
        return (
            f"scale=3840:2160:force_original_aspect_ratio=increase,"
            f"crop=1920:1080,"
            f"zoompan=z='max(zoom-0.0012,1.0)':"
            f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            f"d={int(frames)}:s=1920x1080:fps={fps},format=yuv420p"
        )
    elif cam_type == "panright":
        # 从左向右平移
        pan_px = int(duration * 3)  # 每帧移动3像素
        return (
            f"scale=3840:1080,"
            f"crop=1920:1080:x='min(n*{pan_px},{1920})':y=0,"
            f"fps={fps},format=yuv420p"
        )
    elif cam_type == "panleft":
        # 从右向左平移
        pan_px = int(duration * 3)
        return (
            f"scale=3840:1080,"
            f"crop=1920:1080:x='max(0,{1920}-n*{pan_px})':y=0,"
            f"fps={fps},format=yuv420p"
        )
    elif cam_type == "diagonal":
        # 对角移动
        return (
            f"scale=3840:2160,"
            f"crop=1920:1080:"
            f"x='min(n*2,{1920})':y='min(n*1,{1080})',"
            f"fps={fps},format=yuv420p"
        )

def make_particle_filter(ptype, duration, fps=24):
    """生成粒子叠加层"""
    frames = duration * fps
    if ptype == "gold":
        # 金色光点（暖色）
        return (
            f"color=c=black:s=1920x1080:d={duration}:r={fps},format=rgba,"
            f"geq=r='255':g='220':b='180':"
            f"a='if(lt(random(1),0.015),random(1)*255,0)'"
        )
    elif ptype == "petal":
        # 粉白花瓣（柔美）
        return (
            f"color=c=black:s=1920x1080:d={duration}:r={fps},format=rgba,"
            f"geq=r='255':g='200':b='200':"
            f"a='if(lt(random(1),0.015),random(1)*200,0)'"
        )
    else:
        return None

# ============================================================
# 步骤1：为每张图生成 Ken Burns 动画 + 粒子
# ============================================================
print("\n[1/3] 生成 Ken Burns 动画...")

for i, (name, dur, cam, particle) in enumerate(SEGMENTS, 1):
    num = f"{i:02d}"
    img_path = os.path.join(RAW_DIR, f"{name}.png")
    clip_path = os.path.join(CLIP_DIR, f"clip_{num}.mp4")
    particle_path = os.path.join(CLIP_DIR, f"part_{num}.mp4")

    # 检查图片是否存在（也支持 .jpg）
    if not os.path.exists(img_path):
        img_path = os.path.join(RAW_DIR, f"{name}.jpg")
        if not os.path.exists(img_path):
            print(f"  ⚠️ 未找到 {name}，跳过")
            continue

    # 生成 Ken Burns 动画
    kf = make_kenburns_filter(cam, dur)
    cmd = [
        FFMPEG, "-y", "-loop", "1", "-i", img_path,
        "-vf", kf,
        "-t", str(dur),
        "-c:v", "libx264", "-crf", "20", "-preset", "medium",
        "-an", "-hide_banner", "-loglevel", "warning",
        clip_path
    ]
    subprocess.run(cmd)
    print(f"  {num}/{len(SEGMENTS)} {name} → Ken Burns ({dur}s, {cam})")


# ============================================================
# 步骤1.5：生成粒子叠加层（仅对需要粒子的片段）
# ============================================================
print("\n  生成粒子叠加层...")

particle_clips = []
for i, (name, dur, cam, particle) in enumerate(SEGMENTS, 1):
    num = f"{i:02d}"
    if particle == "none":
        continue

    pf = make_particle_filter(particle, dur)
    if pf:
        particle_path = os.path.join(CLIP_DIR, f"part_{num}.mp4")
        cmd = [
            FFMPEG, "-y", "-f", "lavfi", "-i", pf,
            "-t", str(dur),
            "-c:v", "libx264", "-crf", "25",
            "-an", "-hide_banner", "-loglevel", "warning",
            particle_path
        ]
        subprocess.run(cmd)
        particle_clips.append(num)

print(f"  粒子层完成: {len(particle_clips)} 段")

# ============================================================
# 步骤1.7：应用特殊动画效果（史书展开、剑花等）
# ============================================================
if FX_AVAILABLE:
    print("\n  应用特殊动画效果...")
    fx_results = effects.apply_effects(RAW_DIR, CLIP_DIR)
    # 记录哪些片段被特效替换了（用于后续跳过普通Ken Burns处理）
    fx_names = {name for name, _ in fx_results}
else:
    print("\n  ⚠️ 未找到特效模块，跳过动画效果")
    fx_names = set()

# ============================================================
# 步骤2：合成（Ken Burns + 粒子叠合 + 古风调色 + 字幕 + 音频）
# ============================================================
print("\n[2/3] 合成最终视频...")

# 构建复杂的 filter_complex
# 对于每个片段：Ken Burns 视频 + 粒子叠加（如果有）→ 调色
# 然后用 concat 拼接所有片段

filter_parts = []
concat_inputs = ""
prev_label = ""

for i, (name, dur, cam, particle) in enumerate(SEGMENTS, 1):
    num = f"{i:02d}"
    clip_path = os.path.join(CLIP_DIR, f"clip_{num}.mp4")
    particle_path = os.path.join(CLIP_DIR, f"part_{num}.mp4")

    clip_label = f"c{num}"
    has_particle = os.path.exists(particle_path)

    # Ken Burns 视频输入
    filter_parts.append(f"[{i-1}:v]setpts=PTS-STARTPTS[v{num}];")

    if has_particle:
        # 粒子叠加
        filter_parts.append(
            f"[v{num}]"
            f"[{i-1+len(SEGMENTS)}:v]"
            f"overlay=0:0:shortest=1,"
            f"format=yuv420p[vp{num}];"
        )

    # 古风调色（统一色调）
    grade_filter = (
        "eq=saturation=0.75:contrast=1.08:brightness=-0.02,"
        "colorbalance=rs=0.05:gs=-0.03:bs=-0.08,"
        "vignette=PI/5,"
        "unsharp=3:3:0.7"
    )

    if has_particle:
        filter_parts.append(
            f"[vp{num}]{grade_filter}[g{num}];"
        )
    else:
        filter_parts.append(
            f"[v{num}]{grade_filter}[g{num}];"
        )

# 由于 ffmpeg concat 在复杂滤镜中实现较复杂，
# 改用简单方法：先分别处理每一段，然后 concat 协议拼接

print("  改用分段生成+拼接方式（更稳定）...")

# 对每段：合并 Ken Burns + 粒子 + 调色，输出单独视频
for i, (name, dur, cam, particle) in enumerate(SEGMENTS, 1):
    num = f"{i:02d}"
    clip_path = os.path.join(CLIP_DIR, f"clip_{num}.mp4")
    particle_path = os.path.join(CLIP_DIR, f"part_{num}.mp4")
    output_path = os.path.join(CLIP_DIR, f"graded_{num}.mp4")

    grade_filter = (
        "eq=saturation=0.75:contrast=1.08:brightness=-0.02,"
        "colorbalance=rs=0.05:gs=-0.03:bs=-0.08,"
        "vignette=PI/5,"
        "unsharp=3:3:0.7"
    )

    if os.path.exists(particle_path):
        # 有粒子层：叠加后再调色
        cmd = [
            FFMPEG, "-y",
            "-i", clip_path,
            "-i", particle_path,
            "-filter_complex",
            f"[0:v][1:v]overlay=0:0:shortest=1,{grade_filter},format=yuv420p",
            "-c:v", "libx264", "-crf", "20", "-preset", "medium",
            "-an", "-hide_banner", "-loglevel", "warning",
            output_path
        ]
    else:
        # 无粒子层：直接调色
        cmd = [
            FFMPEG, "-y",
            "-i", clip_path,
            "-vf", f"{grade_filter},format=yuv420p",
            "-c:v", "libx264", "-crf", "20", "-preset", "medium",
            "-an", "-hide_banner", "-loglevel", "warning",
            output_path
        ]

    subprocess.run(cmd)

print("  所有片段合成完成")

# 特效片段覆盖对应普通片段（如果有）
if FX_AVAILABLE and fx_results:
    print("\n  替换特效片段...")
    for name, fx_path in fx_results:
        # 找到这个片段的序号
        for i, (seg_name, _, _, _) in enumerate(SEGMENTS, 1):
            if seg_name == name:
                num = f"{i:02d}"
                target = os.path.join(CLIP_DIR, f"graded_{num}.mp4")
                if os.path.exists(fx_path):
                    subprocess.run(["cp" if os.name != "nt" else "copy",
                                    fx_path, target],
                                   shell=(os.name == "nt"))
                    print(f"   {name} → 替换为特效版")
                break

# ============================================================
# 步骤3：拼接 + 字幕 + 音频
# ============================================================
print("\n[3/3] 拼接 + 字幕 + 音频...")

# 创建 concat 文件列表
concat_list = os.path.join(CLIP_DIR, "concat_list.txt")
with open(concat_list, "w", encoding="utf-8") as f:
    for i in range(1, len(SEGMENTS) + 1):
        num = f"{i:02d}"
        graded_path = os.path.join(CLIP_DIR, f"graded_{num}.mp4")
        if os.path.exists(graded_path):
            f.write(f"file '{graded_path}'\n")

# 第一步：拼接视频
merged = os.path.join(CLIP_DIR, "merged.mp4")
subprocess.run([
    FFMPEG, "-y", "-f", "concat", "-safe", "0",
    "-i", concat_list,
    "-c:v", "libx264", "-crf", "18", "-preset", "medium",
    "-an", "-hide_banner",
    merged
], check=True)

# 检查拼接时长
result = subprocess.run([
    FFMPEG, "-i", merged,
    "-f", "null", "-"
], capture_output=True, text=True)
print("  视频拼接完成")

# 第二步：加字幕 + 合成音频
final_output = os.path.join(OUTPUT_DIR, "yanqingmen_mv_final.mp4")

if os.path.exists(SUBS):
    cmd = [
        FFMPEG, "-y",
        "-i", merged,
        "-i", AUDIO,
        "-vf",
        f"subtitles='{SUBS}':force_style="
        f"'FontName=STKaiti,FontSize=36,PrimaryColour=&HFFFFFF,"
        f"OutlineColour=&H1A1A2E,Outline=3,Shadow=2,MarginV=50'",
        "-c:v", "libx264", "-crf", "18", "-preset", "medium",
        "-c:a", "aac", "-b:a", "320k",
        "-shortest", "-map", "0:v:0", "-map", "1:a:0",
        "-movflags", "+faststart",
        final_output, "-hide_banner"
    ]
else:
    cmd = [
        FFMPEG, "-y",
        "-i", merged,
        "-i", AUDIO,
        "-c:v", "libx264", "-crf", "18", "-preset", "medium",
        "-c:a", "aac", "-b:a", "320k",
        "-shortest", "-map", "0:v:0", "-map", "1:a:0",
        "-movflags", "+faststart",
        final_output, "-hide_banner"
    ]

subprocess.run(cmd, check=True)

# ============================================================
# 完成
# ============================================================
file_size = os.path.getsize(final_output) / (1024 * 1024)
print(f"\n{'='*55}")
print(f"🎉 燕青门 MV 制作完成！")
print(f"{'='*55}")
print(f"📁 输出: {final_output}")
print(f"📏 大小: {file_size:.1f} MB")
print(f"💡 用任何播放器打开即可观看")
print(f"{'='*55}")
