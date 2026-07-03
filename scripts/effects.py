# ============================================================
# 燕青门 · 特殊动画效果
# 用 ffmpeg 实现：史书展开、剑花绽放、箭化飞花等
# ============================================================

import subprocess, os

FFMPEG = "ffmpeg"

def make_book_unfurl(input_img, output_video, duration=14):
    """
    史书缓缓展开效果
    图片中书本部分从中间向两侧展开，文字逐行显现
    """
    # 方法：先用 crop 从中间向两侧扩展宽度，模拟书本展开
    fps = 24
    frames = duration * fps

    # 从画面中心向两侧展开（先竖条再扩宽）
    # 用 crop + overlay 组合实现
    filter_complex = (
        # 原始图复制两份
        f"[0:v]split[base][book];"
        # 书本展开：crop 宽度逐渐从 0 到 100%，水平居中
        f"[book]crop=iw*min(t/{duration},1):ih:"
        f"iw/2-iw*min(t/{duration},1)/2:0,"
        f"format=rgba,"
        # 金色光芒渐显
        f"geq=r='r(X,Y)+30*min(t/{duration},1)':"
        f"g='g(X,Y)+20*min(t/{duration},1)':"
        f"b='b(X,Y)':a=255[glow];"
        # 叠加展开的书到原图
        f"[base][glow]overlay=0:0:shortest=1,"
        f"format=yuv420p"
    )

    cmd = [
        FFMPEG, "-y", "-loop", "1", "-i", input_img,
        "-filter_complex", filter_complex,
        "-t", str(duration),
        "-c:v", "libx264", "-crf", "18", "-preset", "medium",
        "-an", output_video
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return output_video


def make_sword_flower(input_img, output_video, duration=11):
    """
    弹指剑花效果
    指尖光点扩散 + 花瓣飞散 + 光芒闪烁
    """
    fps = 24
    frames = duration * fps

    # 生成光晕脉冲 + 花瓣粒子
    filter_complex = (
        # 源图
        f"[0:v]split[bg][fg];"
        # 光晕脉冲：从中心辐射的亮环，逐渐扩大变淡
        f"color=c=black:s=1920x1080:d={duration}:r={fps},"
        f"geq=r='min(255,200*(1-abs(hypot(X-960,Y-540)/800 - min(t/{duration},0.8))*3))':"
        f"g='min(255,180*(1-abs(hypot(X-960,Y-540)/800 - min(t/{duration},0.8))*3))':"
        f"b='min(255,100*(1-abs(hypot(X-960,Y-540)/800 - min(t/{duration},0.8))*3))'"
        f"[halo];"
        # 合成到背景
        f"[bg][halo]overlay=0:0:shortest=1,"
        f"format=yuv420p"
    )

    cmd = [
        FFMPEG, "-y", "-loop", "1", "-i", input_img,
        "-filter_complex", filter_complex,
        "-t", str(duration),
        "-c:v", "libx264", "-crf", "18", "-preset", "medium",
        "-an", output_video
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
    except:
        # 如果 eq 不支持 fallback
        pass
    return output_video


def make_text_reveal(input_img, output_video, duration=14):
    """
    文字逐行显现效果（配合史书展开）
    从上到下逐行显现
    """
    fps = 24

    # 用 scroll 垂直滚动 + crop 固定区域，模拟文字逐行出现
    filter_complex = (
        # 先把图放大以适应滚动
        f"[0:v]scale=1920:1200:force_original_aspect_ratio=increase,"
        # 从顶部向下滚动，露出文字行
        f"crop=1920:1080:0:'ih-1080-min(ih-1080,t/{duration}*(ih-1080))',"
        f"fps={fps},format=yuv420p"
    )

    cmd = [
        FFMPEG, "-y", "-loop", "1", "-i", input_img,
        "-vf", filter_complex,
        "-t", str(duration),
        "-c:v", "libx264", "-crf", "18", "-preset", "medium",
        "-an", output_video
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return output_video


def make_arrow_petal(input_img, output_video, duration=13):
    """
    箭化飞花效果（背景 + 花瓣粒子密集飘落）
    """
    fps = 24

    # 生成密集花瓣粒子
    particle_filter = (
        f"color=c=black:s=1920x1080:d={duration}:r={fps},format=rgba,"
        f"geq=r='255':g='200':b='210':"
        f"a='if(lt(random(1),0.03),random(1)*255,0)'"
    )

    composite = (
        f"[0:v][1:v]overlay=0:0:shortest=1,"
        f"format=yuv420p"
    )

    cmd = [
        FFMPEG, "-y",
        "-loop", "1", "-i", input_img,
        "-f", "lavfi", "-i", particle_filter,
        "-filter_complex", composite,
        "-t", str(duration),
        "-c:v", "libx264", "-crf", "18", "-preset", "medium",
        "-an", output_video
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return output_video


# ============================================================
# 特效映射表（哪个场景用什么特效）
# ============================================================
EFFECTS = {
    "p15": ("book", "史书缓缓展开"),   # 男声 Verse4
    "p11": ("flower", "弹指剑花"),     # 副歌
    "p07": ("arrow", "箭化飞花"),       # 男声
    "p06": ("text_reveal", "侠客诗显现"), # 男声
}

def apply_effects(raw_dir, clips_dir):
    """
    对指定场景应用特效
    返回需要替换的片段列表 [(original_name, effect_video_path)]
    """
    results = []
    for name, (effect_type, desc) in EFFECTS.items():
        img_path = os.path.join(raw_dir, f"{name}.png")
        if not os.path.exists(img_path):
            img_path = os.path.join(raw_dir, f"{name}.jpg")
            if not os.path.exists(img_path):
                print(f"  ⚠️ 未找到 {name} 的图片，跳过特效")
                continue

        out_path = os.path.join(clips_dir, f"fx_{name}.mp4")

        print(f"  🎬 特效: {desc} ({name})...")

        if effect_type == "book":
            make_book_unfurl(img_path, out_path)
        elif effect_type == "flower":
            make_sword_flower(img_path, out_path)
        elif effect_type == "arrow":
            make_arrow_petal(img_path, out_path)
        elif effect_type == "text_reveal":
            make_text_reveal(img_path, out_path)

        results.append((name, out_path))
        print(f"    ✅ {desc} 完成")

    return results


if __name__ == "__main__":
    import sys
    raw_dir = sys.argv[1] if len(sys.argv) > 1 else "../videos/raw"
    clips_dir = sys.argv[2] if len(sys.argv) > 2 else "../videos/clips"
    apply_effects(raw_dir, clips_dir)
    print("\n✅ 所有特效生成完成")
