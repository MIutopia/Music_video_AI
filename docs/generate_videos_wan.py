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
    # (目标时长, 镜数, 镜1, 镜2, 镜3)
    (13, 3,
     "秋日古城全景航拍，金色银杏覆青瓦，斑驳城墙蜿蜒如龙，远山云雾，暖金夕阳从城门透出，镜头缓慢推进",
     "古城墙平视，青砖斑驳苔痕，墙头秋草摇曳，远处飞檐若隐若现，光影柔和",
     "青石板路反射夕阳，红灯笼随风轻摆，落叶飘过，人影稀疏，宁静古朴"),

    (13, 3,
     "古城门仰拍特写，门钉铜绿，石狮威严，门缝透暖光，青松枝桠探墙头，秋叶落石阶",
     "石狮头部特写，鬃毛纹理清晰，眼神威严，背景虚化城门，光影斑驳",
     "门缝透光近景，厚木门微开，暖光从缝隙照亮石阶，青苔蔓延，松针散落"),

    (12, 3,
     "老茶馆内景，白发说书人执折扇坐木椅，青瓷茶盏热气袅袅，竹影投纸窗，暖黄烛光",
     "说书人面部特写，眼神深邃，折扇半遮面，烛光映皱纹，叙事感",
     "茶盏特写，青瓷茶汤微漾，热气升腾，背景虚化说书人剪影，静谧"),

    (12, 3,
     "月洞门框景，翠竹摇曳，石径蜿蜒，燕青门匾额隐约可见，雨后青石倒映天光，青绿主调",
     "青竹特写，叶沾雨滴垂，竹竿挺拔，背景虚化白墙，清新雅致",
     "雨后石阶，水洼倒映天色，光影斑驳，空无人迹，静"),

    (13, 3,
     "旧木案上泛黄经络图展开，银针草药半烛，窗外光照卷轴，石阶剑痕，暖褐暗红",
     "经络图特写，墨线勾勒穴位，朱砂标注，烛光摇曳映照，古朴神秘",
     "石阶剑痕特写，深浅刻痕交错，青苔蔓延隙缝，阳光斜照明暗，沧桑"),

    (13, 3,
     "大远景，白衣侠客立于山巅巨岩，背对画面，前方云海翻腾，丁达尔金光斜射，壮阔",
     "群山层叠云海翻涌大景，侠客渺小剪影融入天地，义薄云天气势",
     "侠客侧身握剑，风吹发丝，眼神远眺，金色光勾勒轮廓，坚毅"),

    (10, 2,
     "侠客侧身拉弓如满月，箭已离弦化作漫天粉白花瓣旋舞，暮色晚霞为背景，动势",
     "花瓣飞花全景，粉白花瓣旋舞如雪，侠客剪影立于花雨中，晚霞背景，诗意浪漫"),

    (13, 3,
     "侠客低首凝视长剑，剑身映眉眼，若有所思，留白背景流云，半明半暗",
     "剑身特写，寒光凛冽映出侠客眼眸，剑刃纹理清晰，沉思氛围",
     "空镜，流云掠过山巅，天地苍茫无人物，留白——何以为侠"),

    (9, 2,
     "燕青门全景，青松列植广场，门匾高悬，主殿飞檐翘角，天际晚霞绚烂，金色青绿",
     "门匾特写，燕青门三字苍劲，金漆斑驳，晚霞映照，庄严厚重"),

    (11, 2,
     "侠客张开双臂面向锦绣山河，金色阳光沐浴，广角构图，史诗感，胸怀天下",
     "山河全景俯拍，群山层叠河流蜿蜒，侠客渺小身影立于天地间"),

    (11, 2,
     "指尖轻弹，银色剑气绽放成半透明水墨剑花，墨色到金色渐变，光芒四射",
     "剑花绽放全景，光芒中侠客剪影，花瓣飞散，唯美震撼"),

    (15, 3,
     "璀璨银河横跨夜空，星光倒映蜿蜒江河，冷蓝深紫夜色，萤火几点",
     "一人独坐古塔上仰望星空，背影孤独，夜风轻拂衣袂，情感锚点",
     "江面倒映星空，波光粼粼映出银河，远处山峦如墨，静谧深邃"),

    (8, 2,
     "银河旋转延时感，星轨流动如瀑布倾泻，古塔剪影静立，动静对比",
     "山峦层叠如黛，夜色苍茫，河面银光点点"),

    (9, 2,
     "惊涛拍岸卷千堆雪，巨大礁石屹立浪中纹丝不动，远景山河辽阔",
     "浪花特写，巨浪拍击礁石瞬间，水花飞溅如碎玉，力量爆发"),

    (14, 3,
     "泛黄史书展开，竖排墨字工整，两侧烛光摇曳，历代侠士剪影叠画",
     "字迹特写，墨字苍劲，纸张泛黄，侠士剪影浮现于书页之上",
     "金色光芒从书页升腾如灵魂，烛火摇曳，神圣肃穆"),

    (9, 2,
     "从燕青门内向外望，门槛光影交错，门外山河金辉盛世，温暖金色调",
     "门外山河全景，门框构图，晚霞漫天，开阔深远"),

    (13, 3,
     "繁华古都街景全景，商铺林立，红灯笼连成星河，金色夕阳笼罩全城",
     "街市中景，行人谈笑，孩童追逐嬉戏，生活气息浓郁，温暖富足",
     "灯笼特写，暖光映照，背景虚化人影，金色调"),

    (11, 2,
     "夕阳下男女并肩剪影，头发由黑渐白诗意过渡，暖金色调温柔浪漫",
     "落日余晖全景，二人渺小剪影，大面积天空留白，岁月静好"),

    (14, 3,
     "古风院落错落，屋顶炊烟袅袅，孩童追逐嬉戏，秋日暖阳洒满庭院",
     "孩童嬉戏近景，追逐欢笑，背景虚化院落炊烟，暖阳活泼",
     "老人坐古树下含笑，鸡犬相闻，岁月安然，祥和收束"),

    (14, 3,
     "草原天际线，双人策马奔腾，骏马腾空，夕阳金光洒满草原，广角跟拍",
     "马蹄飞扬特写，马鬃飘动，肌肉动感，速度张力",
     "双人骑马侧拍，衣袂飞扬，草原辽阔背景，自由豪迈"),

    (14, 3,
     "双人骑马远去，背影在地平线越来越小，融入巨大金色落日，三分法构图",
     "远景晚霞漫天，二人剪影即将消失，留白意蕴",
     "空镜，落日半沉地平线，余晖渲染天际，天地宁静——终"),
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

for i, scene in enumerate(SCENES, 1):
    target_dur, num_clips = scene[0], scene[1]
    prompts_clips = list(scene[2:2+num_clips])

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
