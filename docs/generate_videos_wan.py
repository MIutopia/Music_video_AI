# ============================================================
# 燕青门 · Wan2.2-TI2V-5B 文生视频（多段拼接版）
# 每段生成 2-3 个 5秒视频，拼接后仅需微慢放
# 运行环境：百度 AI Studio（24GB VRAM）
# ============================================================

import torch
from modelscope import pipeline
from modelscope.outputs import OutputKeys
import os, gc, time, imageio, shutil, subprocess

FFMPEG = "ffmpeg"

# 清理旧缓存
old_cache = "/mnt/workspace/.cache/modelscope/Wan-AI"
if os.path.exists(old_cache):
    shutil.rmtree(old_cache)

# ============================================================
# 1. 加载模型
# ============================================================
print("加载 Wan2.2-TI2V-5B ...")
pipe = pipeline("text-to-video", model="Wan-AI/Wan2.2-TI2V-5B", device="cuda")
print("✅ 加载成功\n")

# ============================================================
# 2. 分镜定义（每段目标时长 + 生成几个5秒视频）
# ============================================================
SCENES = [
    # (目标时长, 生成段数, Prompt视角1, Prompt视角2)
    (13, 3, "秋日古城全景，金色银杏覆青瓦，斑驳城墙蜿蜒，夕阳暖光从城门透出", "古城墙特写，青砖苔痕，红叶从墙头垂落，秋风吹过落叶飞舞"),
    (13, 3, "古城门仰拍，门钉铜绿，石狮威严，门缝透暖光，青松探墙", "古城门内部视角，透过门缝看到庭院深处暖光，石阶上落叶"),
    (12, 2, "老茶馆内景，白发说书人执折扇，青瓷茶盏热气袅袅", "茶馆窗边，竹影投在纸窗上，茶烟缭绕，光线柔和温暖"),
    (12, 2, "幽深庭院，月洞门，燕青门匾额，青竹探墙，雨后青石路", "庭院角落，石灯青苔，雨珠从屋檐滴落，水面涟漪"),
    (12, 2, "旧木案上泛黄经络图展开，银针草药，窗前光影交错", "石阶上剑痕特写，雨水流过剑痕，倒映天空"),
    (13, 3, "白衣侠客立山巅，背对画面，长袍翻飞，云海金光", "侠客侧影，风吹衣袂，手握剑柄，眼神望向远方"),
    (10, 2, "侠客拉弓如满月，箭尖寒光，花瓣纷飞", "弓箭特写，手指松开弓弦瞬间，花瓣在空中绽放"),
    (13, 3, "侠客低首凝视长剑，剑身映眉眼，留白背景", "剑锋特写，寒光流转，映出侠客模糊面庞"),
    (9, 2, "燕青门全景，青松列植，门匾高悬，晚霞绚烂", "燕青门内仰望飞檐，檐角铜铃，夕阳穿过雕花窗"),
    (11, 2, "侠客张开双臂面向山河，金色阳光沐浴", "壮阔山河大远景，人物立于天地间，渺小而坚定"),
    (11, 2, "指尖轻弹，银色剑气绽放成水墨剑花", "剑花特写，墨色到金色渐变，光芒四射"),
    (15, 3, "深夜星河如瀑布倾泻，银河横跨天际", "古塔剪影，萤火虫在夜色中飞舞，星光倒映水面"),
    (12, 2, "壮阔山水，星河倒映奔腾江河，山峦层叠", "河面波光潋滟，水天一色，清冷蓝紫色调"),
    (12, 2, "惊涛骇浪拍击礁石，浪花飞溅如碎玉", "礁石屹立千年，远景山河与暗蓝夜空"),
    (14, 3, "泛黄史书展开，金色光芒从书页升腾", "烛光摇曳，墨字苍劲，侠士剪影叠画于书页"),
    (9, 2, "从燕青门内向外望，门外山河金辉", "门槛光影交错，青松晚霞，温暖金色"),
    (11, 2, "繁华古都街市，商铺林立，灯笼连成星河", "市井近景，孩童追逐，行人谈笑，夕阳笼罩"),
    (11, 2, "夕阳下男女并肩剪影，头发从黑到银白", "落日余晖剪影，温柔浪漫，大面积天空留白"),
    (14, 3, "古风院落，炊烟袅袅，孩童嬉戏，老人含笑", "院落秋色，柿子满枝，鸡犬相闻，暖阳洒落"),
    (14, 3, "壮阔草原，双人策马奔腾，夕阳金光照草原", "马匹特写，四蹄腾空，衣袂飞扬，速度感"),
    (14, 3, "骑马远去背影融入金色落日，晚霞漫天", "地平线远景，人影越来越小，融入余晖，留白意境"),
]

# ============================================================
# 3. 生成每段的多个5秒视频并拼接
# ============================================================
RAW_DIR = "/mnt/workspace/yanqingmen_videos_raw"
SEG_DIR = "/mnt/workspace/yanqingmen_videos"
os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(SEG_DIR, exist_ok=True)

total = len(SCENES)
start_time = time.time()
clip_count = 0

for i, (target_dur, num_clips, prompt1, prompt2) in enumerate(SCENES, 1):
    prompts_clips = [prompt1]
    if num_clips >= 2:
        prompts_clips.append(prompt2)
    if num_clips >= 3:
        prompts_clips.append(f"{prompt1}，不同角度")

    clip_files = []

    for j, p in enumerate(prompts_clips):
        clip_count += 1
        print(f"[{i:02d}/{total}] 视频 {j+1}/{num_clips}")

        result = pipe({
            'text': p,
            'num_frames': 120,
            'width': 1280,
            'height': 704,
        })
        frames = result[OutputKeys.OUTPUT_VIDEO]

        tmp = f"{RAW_DIR}/tmp_{i:02d}_{j}.mp4"
        imageio.mimsave(tmp, frames, fps=24, codec="libx264", quality=8)
        clip_files.append(tmp)

        torch.cuda.empty_cache()
        gc.collect()

    # 拼接多个5秒视频
    if num_clips == 1:
        final_raw = clip_files[0]
    else:
        final_raw = f"{RAW_DIR}/combined_{i:02d}.mp4"
        concat_file = f"{RAW_DIR}/list_{i:02d}.txt"
        with open(concat_file, "w") as f:
            for cf in clip_files:
                f.write(f"file '{cf}'\n")
        subprocess.run([
            FFMPEG, "-y", "-f", "concat", "-safe", "0",
            "-i", concat_file,
            "-c:v", "libx264", "-crf", "18", "-preset", "medium",
            "-an", "-hide_banner", "-loglevel", "warning",
            final_raw
        ], check=True)

    # 计算慢放因子
    total_raw = num_clips * 5
    ratio = target_dur / total_raw

    print(f"  → 原始{total_raw}s → 目标{target_dur}s (x{ratio:.2f})")

    if abs(ratio - 1.0) < 0.05:
        # 几乎不需要慢放，直接复制
        shutil.copy(final_raw, f"{SEG_DIR}/v{i:02d}.mp4")
    else:
        new_fps = round(24 * ratio)
        subprocess.run([
            FFMPEG, "-y", "-i", final_raw,
            "-vf",
            f"minterpolate=fps={new_fps}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir,"
            f"format=yuv420p",
            "-t", str(target_dur),
            "-c:v", "libx264", "-crf", "18", "-preset", "medium",
            "-an", "-hide_banner", "-loglevel", "warning",
            f"{SEG_DIR}/v{i:02d}.mp4"
        ], check=True)

    print(f"  ✅ v{i:02d}.mp4 ({target_dur}s)")

elapsed = time.time() - start_time
print(f"\n{'='*50}")
print(f"🎉 全部完成！共 {total} 段视频")
print(f"⏱ 耗时: {elapsed:.0f} 秒")
print(f"📁 输出: {SEG_DIR}")
print(f"💡 下载 v01~v{total:02d}.mp4 到 videos/raw/")
print(f"   然后运行: python scripts/build_mv.py")
print(f"{'='*50}")
