# ============================================================
# 燕青门 · SDXL 批量生成 21 张古风图（音频情感驱动版）
# 运行环境：百度 AI Studio（V100 16GB）
# 使用方法：python generate_images.py
# ============================================================

# 安装依赖（首次运行需取消注释）
# import subprocess
# subprocess.run("pip install diffusers transformers accelerate peft safetensors librosa -q".split())

import torch
from diffusers import StableDiffusionXLPipeline
import os, gc, time

# ============================================================
# 设置国内镜像源（AI Studio 无法直连 HuggingFace）
# ============================================================
# 用 ModelScope（魔搭），阿里云内部直连，无需翻墙
# 如果 ModelScope 也未安装，先 pip install modelscope
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

# ============================================================
# 0. 输出目录
# ============================================================
OUTPUT_DIR = "/mnt/workspace/yanqingmen"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ============================================================
# 0.5 音频情感特征（预分析，无需librosa）
# 数据来自之前成功的音频分析运行
# ============================================================
audio_features = [
    # (rms, spectral, mood, tone)
    (0.059, 2386, "静谧空灵，意境悠远，quiet ethereal", "暖金色调，暖色为主"),
    (0.096, 2296, "平缓叙述，宁静致远，calm narrative", "暖金色调，暖色为主"),
    (0.074, 3182, "静谧空灵，意境悠远，quiet ethereal", "中性色调，青绿为主"),
    (0.091, 2809, "平缓叙述，宁静致远，calm narrative", "中性色调，青绿为主"),
    (0.099, 3038, "平缓叙述，宁静致远，calm narrative", "中性色调，青绿为主"),
    (0.113, 2920, "平缓叙述，宁静致远，calm narrative", "中性色调，青绿为主"),
    (0.131, 2924, "温暖舒展，情绪饱满，warm emotional", "中性色调，青绿为主"),
    (0.129, 2760, "温暖舒展，情绪饱满，warm emotional", "中性色调，青绿为主"),
    (0.139, 2991, "温暖舒展，情绪饱满，warm emotional", "中性色调，青绿为主"),
    (0.140, 2705, "温暖舒展，情绪饱满，warm emotional", "中性色调，青绿为主"),
    (0.136, 2911, "温暖舒展，情绪饱满，warm emotional", "中性色调，青绿为主"),
    (0.139, 2598, "温暖舒展，情绪饱满，warm emotional", "中性色调，青绿为主"),
    (0.114, 3061, "平缓叙述，宁静致远，calm narrative", "中性色调，青绿为主"),
    (0.114, 3277, "平缓叙述，宁静致远，calm narrative", "中性色调，青绿为主"),
    (0.124, 3080, "温暖舒展，情绪饱满，warm emotional", "中性色调，青绿为主"),
    (0.144, 3202, "温暖舒展，情绪饱满，warm emotional", "中性色调，青绿为主"),
    (0.154, 2976, "温暖舒展，情绪饱满，warm emotional", "中性色调，青绿为主"),
    (0.149, 3309, "温暖舒展，情绪饱满，warm emotional", "中性色调，青绿为主"),
    (0.148, 3261, "温暖舒展，情绪饱满，warm emotional", "中性色调，青绿为主"),
    (0.120, 3366, "温暖舒展，情绪饱满，warm emotional", "中性色调，青绿为主"),
    (0.116, 2923, "平缓叙述，宁静致远，calm narrative", "中性色调，青绿为主"),
]
print("✅ 音频情感特征已加载（21段预分析数据）\n")

# ============================================================
# 1. 加载模型（从 ModelScope 国内镜像下载）
# ============================================================
print("加载 SDXL 模型（从 ModelScope 下载，首次约 7GB）...")

try:
    from modelscope import snapshot_download
    model_path = snapshot_download('AI-ModelScope/stable-diffusion-xl-base-1.0')
    print(f"模型缓存路径: {model_path}")
except ImportError:
    print("ModelScope 未安装，尝试从 HuggingFace 镜像下载...")
    model_path = "stabilityai/stable-diffusion-xl-base-1.0"

pipe = StableDiffusionXLPipeline.from_pretrained(
    model_path,
    torch_dtype=torch.float16,
    variant="fp16",
    use_safetensors=True
)
pipe.to("cuda")
pipe.enable_attention_slicing()
pipe.enable_vae_slicing()

print(f"✅ 模型加载完成，显存: {torch.cuda.memory_allocated()/1024**3:.1f}GB\n")

# ============================================================
# 2. 统一风格前缀
# ============================================================
STYLE_PREFIX = "古风国画，青绿山水与水墨淡彩结合，色彩雅致以青绿赭石为主调，清透留白，工笔与写意结合，人物典雅，场景开阔，光影柔和如绢本设色，16:9横轴，诗意叙事感，"

MASTER_SEED = 42

# ============================================================
# 3. 21 条分镜 Prompt（每张图按音频分析结果动态调色/调情绪）
# ============================================================
scene_prompts = [
    # 前奏（S01-S02）
    "秋日古城全景航拍视角，金色银杏叶覆满青瓦屋顶，斑驳城墙蜿蜒如龙，远处青山云雾缭绕，暖金夕阳光从城门洞透出，画面宁静悠远，留白构图",
    "古城门特写仰拍，门钉铜绿斑驳，石狮威严肃穆，门缝透出院内暖光，青松枝桠从墙头探出，秋叶飘落在石阶上，庄重古朴，岁月沉淀感",

    # 女声 Verse1（S03-S05）
    "老茶馆内景，白发说书人穿灰长衫坐木椅上手执折扇，方桌青瓷茶盏热气袅袅，窗外竹影投在纸窗，暖黄烛光，光线柔和，叙事感",
    "幽深庭院月洞门，门楣隐约可见燕青门匾额，青竹几竿探出院墙，石灯青苔，雨后青石路倒映天光，青绿主调",
    "旧木案上泛黄经络图卷轴展开，旁有银针袋石臼草药半烛，窗外天光照在卷轴上，石阶上浅浅剑痕，暖褐暗红调，古朴神秘",

    # 男声 Verse2（S06-S08）
    "白衣侠客立于山巅巨岩，背对画面，长袍劲风翻飞，腰佩古剑，前方云海翻腾层叠远山，金色丁达尔光斜射，壮阔豪情，气势磅礴",
    "侠客侧身拉弓如满月，弓弦已松，箭矢离弦化作漫天粉白花瓣旋舞，背景暮色远山晚霞，动静结合，浪漫与力量，爆发力十足",
    "侠客低首凝视长剑，剑身映出眉眼，若有所思，背景大片留白山色流云，光影半明半暗，深沉内省",

    # 副歌 Chorus1（S09-S11）
    "大气全景，燕青门宏伟建筑群，门前广场青松列植，门匾高悬，远处主殿飞檐翘角，天际晚霞绚烂，金色青绿交织，恢弘壮丽",
    "侠客立于天地间张开双臂面向锦绣山河，脚下大地辽阔，苍穹无垠，金色阳光沐浴全身，广角构图，史诗感，胸怀天下",
    "指尖轻弹，银色剑气从指尖绽放成一朵半透明水墨剑花，花瓣墨色到金色渐变，光芒四射，极致唯美，视觉冲击",

    # 间奏（S12）
    "深夜山巅，满天星河璀璨如瀑布倾泻，银河横跨天际，星光倒映在蜿蜒江河中，近处古塔剪影，远处山峦如墨，萤火几点，空灵静谧",

    # 女声 Verse3（S13-S14）
    "壮阔山水之间，皎洁星河倒映在奔腾江河中，两岸山峦层叠如黛，天地苍茫，河面水光潋滟波光粼粼，夜空深邃，清冷蓝紫调",
    "惊涛骇浪拍击海中礁石，礁石屹立千百年纹丝不动，浪花飞溅如碎玉崩裂，远景壮丽山河与暗蓝夜空，力量感，永恒与坚韧",

    # 男声 Verse4（S15）
    "泛黄史书在案上展开，竖排墨字工整苍劲，书页间一缕金色光芒如灵魂升腾而上，两侧烛光摇曳，历代侠士剪影叠画，神圣肃穆",

    # 副歌 Chorus2（S16-S18）
    "从燕青门内向外望，门槛内外光影交错，门外壮丽山河与金辉盛世，青松挺立，晚霞漫天，温暖金色调，传承与希望",
    "繁华古都街市全景，市井安宁商铺林立，红灯笼暖光连成星河，行人谈笑孩童追逐嬉戏，金色夕阳笼罩全城，温暖富足的太平景象",
    "夕阳下男女二人并肩剪影，头发由黑渐银白的诗意过渡，暖金色调温柔浪漫，大面积落日余晖与细小的人影形成强烈对比",

    # 桥段（S19）
    "错落有致的古风院落，屋顶炊烟袅袅升腾，孩童在院中嬉戏追逐，老人坐古树下含笑看着，鸡犬相闻，秋日暖阳洒满庭院，祥和安宁",

    # 尾声（S20-S21）
    "壮阔草原天际线，一男一女双人策马奔腾向远方，骏马腾空四蹄飞扬，衣袂飘举，夕阳金黄光芒洒满广袤草原，广角跟拍，自由速度",
    "双人骑马远去的背影在地平线上越来越小，逐渐融入巨大的金色落日之中，漫天绚烂暖色晚霞，画面三分法构图，悠远意境，结尾留白余韵"
]

# ============================================================
# 4. 批量生成（每张图加入音频情感修饰）
# ============================================================

total = len(scene_prompts)
start_time = time.time()

for i, prompt in enumerate(scene_prompts, 1):
    _, _, mood, tone = audio_features[i-1]

    # 合成 final prompt = 风格前缀 + 场景描述 + 音频情感 + 色调
    full_prompt = f"{STYLE_PREFIX}{prompt}，{tone}，{mood}"

    generator = torch.Generator("cuda").manual_seed(MASTER_SEED + i)

    print(f"[{i:02d}/{total}] 🎵 {mood[:16]}...")

    img = pipe(
        full_prompt,
        num_inference_steps=25,
        guidance_scale=7.5,
        width=1024,
        height=576,
        generator=generator,
    ).images[0]

    img.save(f"{OUTPUT_DIR}/p{i:02d}.png")
    print(f"  ✅ p{i:02d}.png")

    del img
    torch.cuda.empty_cache()
    gc.collect()

elapsed = time.time() - start_time
print(f"\n{'='*50}")
print(f"🎉 全部完成！共 {total} 张图")
print(f"⏱  耗时: {elapsed:.0f} 秒 (约 {elapsed/total:.0f} 秒/张)")
print(f"📁 输出: {OUTPUT_DIR}")
print(f"{'='*50}")

# 输出文件清单
print("\n文件清单:")
for f in sorted(os.listdir(OUTPUT_DIR)):
    size_kb = os.path.getsize(f"{OUTPUT_DIR}/{f}") / 1024
    print(f"  {f}  ({size_kb:.0f}KB)")
print(f"\n💡 图片保存在: {OUTPUT_DIR}")
print("请使用 AI Studio 的文件浏览器下载到本地")
