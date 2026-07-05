# ============================================================
# 燕青门 · Wan2.1-14B 文生视频（并行方案2）
# 运行环境：百度 AI Studio（24GB VRAM）
# 使用 ModelScope 原生推理接口（非 diffusers）
# ============================================================

# 安装依赖（首次运行）
# pip install modelscope torch -q

import torch
from modelscope import pipeline, snapshot_download
from modelscope.outputs import OutputKeys
import os, gc, time, imageio
import numpy as np

# ============================================================
# 1. 加载 Wan2.1-14B（ModelScope 原生 pipeline）
# ============================================================
print("加载 Wan2.1-14B（ModelScope 原生推理）...")

# 方案A: 用 ModelScope pipeline（首选）
try:
    pipe = pipeline(
        "text-to-video",
        model="Wan-AI/Wan2.1-T2V-14B",
        device="cuda",
        torch_dtype=torch.bfloat16
    )
    print("✅ Wan2.1 加载成功（ModelScope pipeline）")
except Exception as e:
    print(f"ModelScope pipeline 失败: {e}")
    print("尝试方案B: snapshot_download + 手动加载...")

    # 方案B: 下载后手动指定路径
    model_dir = snapshot_download('Wan-AI/Wan2.1-T2V-14B')
    pipe = pipeline(
        "text-to-video",
        model=model_dir,
        device="cuda"
    )
    print("✅ Wan2.1 加载成功（本地路径）")

# ============================================================
# 2. Prompt（中文 Prompt，Wan2.1 中文理解强于 SDXL）
# ============================================================
prompts = [
    # S01-S02 前奏
    "秋日古城全景，金色银杏覆青瓦，斑驳城墙蜿蜒，夕阳暖光从城门透出，云雾缭绕远山，镜头缓慢推进",
    "古城门仰拍特写，门钉铜绿，石狮威严，门缝透暖光，青松枝桠探出墙头，秋叶飘落石阶，岁月感",

    # S03-S05 女声 Verse1
    "老茶馆内景，白发说书人执折扇坐木椅，青瓷茶盏热气袅袅，窗外竹影投纸窗，暖黄烛光柔和",
    "幽深庭院月洞门，燕青门匾额隐约可见，青竹探墙，石灯青苔，雨后青石倒映天光，青绿调",
    "旧木案上泛黄经络图卷轴展开，银针草药半烛，窗外天光照卷轴，石阶剑痕，古朴神秘",

    # S06-S08 男声 Verse2
    "白衣侠客立山巅巨岩，背对画面，长袍劲风翻飞，云海翻腾远山层叠，丁达尔金光斜射，壮阔豪情",
    "侠客侧身拉弓满月，弓弦已松箭矢离弦，箭化漫天粉白花瓣旋舞，暮色远山晚霞，浪漫与力量",
    "侠客低首凝视长剑，剑身映眉眼若有所思，背景留白山色流云，光影半明半暗，深沉内省",

    # S09-S11 副歌 Chorus1
    "燕青门宏伟建筑群全景，广场青松列植，门匾高悬，主殿飞檐翘角，晚霞绚烂，金色青绿交织",
    "侠客立天地间张开双臂面向锦绣山河，脚下大地辽阔苍穹无垠，金色阳光沐浴全身，史诗感",
    "指尖轻弹，银色剑气绽放成半透明水墨剑花，花瓣墨色到金色渐变，光芒四射，极致唯美",

    # S12 间奏
    "深夜山巅，满天星河如瀑布倾泻，银河横跨天际，星光倒映江河，古塔剪影，萤火几点，空灵静谧",

    # S13-S14 女声 Verse3
    "壮阔山水间，皎洁星河倒映奔腾江河，两岸山峦层叠如黛，河面波光潋滟，夜空深邃，清冷蓝紫",
    "惊涛骇浪拍击礁石，礁石屹立千年纹丝不动，浪花飞溅如碎玉，远景山河与暗蓝夜空，力量感",

    # S15 男声 Verse4
    "泛黄史书在案上展开，竖排墨字苍劲，书页间金色光芒如灵魂升腾，烛光摇曳，侠士剪影叠画，神圣",

    # S16-S18 副歌 Chorus2
    "从燕青门内向外望，门槛内外光影交错，门外壮丽山河金辉盛世，青松晚霞，温暖金色传承",
    "繁华古都街市，市井安宁商铺林立，红灯笼暖光连成星河，行人谈笑孩童追逐，金色夕阳笼罩",
    "夕阳下男女二人并肩剪影，头发由黑渐银白诗意过渡，暖金温柔浪漫，落日余晖与人影对比",

    # S19 桥段
    "古风院落错落有致，屋顶炊烟袅袅，孩童院中嬉戏，老人古树下含笑，鸡犬相闻，秋日暖阳祥和",

    # S20-S21 尾声
    "壮阔草原天际线，双人策马奔腾向远方，骏马腾空四蹄飞扬，夕阳金黄洒满草原，自由速度",
    "双人骑马远去背影在地平线越来越小，融入巨大金色落日，漫天绚烂晚霞，结尾留白余韵"
]

# ============================================================
# 3. 批量生成视频
# ============================================================
OUTPUT_DIR = "/mnt/workspace/yanqingmen_videos"
os.makedirs(OUTPUT_DIR, exist_ok=True)

total = len(prompts)
start_time = time.time()

for i, prompt in enumerate(prompts, 1):
    print(f"[{i:02d}/{total}] 生成视频...")

    # 调用 ModelScope pipeline
    result = pipe({
        'text': prompt,
        'num_frames': 81,     # ~5秒 @ 16fps
        'width': 832,
        'height': 480,
    })

    frames = result[OutputKeys.OUTPUT_VIDEO]  # numpy array

    out_path = f"{OUTPUT_DIR}/v{i:02d}.mp4"
    imageio.mimsave(out_path, frames, fps=16, codec="libx264", quality=8)
    print(f"  ✅ v{i:02d}.mp4")

    torch.cuda.empty_cache()
    gc.collect()

elapsed = time.time() - start_time
print(f"\n{'='*50}")
print(f"🎉 全部完成！共 {total} 段视频")
print(f"⏱ 耗时: {elapsed:.0f} 秒")
print(f"📁 输出: {OUTPUT_DIR}")
print(f"{'='*50}")
