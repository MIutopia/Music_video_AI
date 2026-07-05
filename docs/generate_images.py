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
    (0.059, 2386, "宁静", "暖色"),
    (0.096, 2296, "平缓", "暖色"),
    (0.074, 3182, "宁静", "中性"),
    (0.091, 2809, "平缓", "中性"),
    (0.099, 3038, "平缓", "中性"),
    (0.113, 2920, "平缓", "中性"),
    (0.131, 2924, "温暖", "中性"),
    (0.129, 2760, "温暖", "中性"),
    (0.139, 2991, "温暖", "中性"),
    (0.140, 2705, "温暖", "中性"),
    (0.136, 2911, "温暖", "中性"),
    (0.139, 2598, "温暖", "中性"),
    (0.114, 3061, "平缓", "中性"),
    (0.114, 3277, "平缓", "中性"),
    (0.124, 3080, "温暖", "中性"),
    (0.144, 3202, "温暖", "中性"),
    (0.154, 2976, "温暖", "中性"),
    (0.149, 3309, "温暖", "中性"),
    (0.148, 3261, "温暖", "中性"),
    (0.120, 3366, "温暖", "中性"),
    (0.116, 2923, "平缓", "中性"),
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
STYLE_PREFIX = ("Chinese ink wash painting, ancient Chinese aesthetic, 16:9, "
    "no text, no calligraphy, no seal stamp, no signature, no watermark")

MASTER_SEED = 42

# ============================================================
# 3. 21 条分镜 Prompt（每张图按音频分析结果动态调色/调情绪）
# ============================================================
scene_prompts = [
    # 前奏（S01-S02）
    "ancient Chinese autumn city panoramic aerial view, golden gingko leaves on blue tiled roofs, weathered city wall, misty mountains distant, warm golden sunset light, serene timeless mood",
    "ancient city gate close-up low angle, bronze door nails green patina, stone lion, warm light through door crack, pine branches over wall, autumn leaves on steps, sense of history",

    # 女声 Verse1（S03-S05）
    "traditional Chinese teahouse interior, old storyteller in grey robe sitting on wooden chair holding fan, celadon tea cup with steam, bamboo shadows on paper window, warm candlelight, soft atmosphere",
    "deep courtyard with moon gate, plaque with Chinese characters partially visible, bamboo over wall, stone lantern with moss, rain-washed path reflecting sky, jade green tones, serene",
    "old wooden desk with yellowed medical scroll unrolled, acupuncture needles, stone mortar with herbs, candle burning, light through window on scroll, sword marks on stone steps, ancient mystery",

    # 男声 Verse2（S06-S08）
    "white-robed martial arts hero on mountain peak, back facing viewer, robe billowing in wind, ancient sword at waist, sea of clouds below, golden rays piercing clouds, epic grandeur",
    "martial artist drawing bow to full moon, arrow released transforming into pink and white flower petals swirling in air, dusk sky with colorful sunset clouds, dynamic romantic powerful",
    "hero gazing down at his longsword, blade reflecting his eyes, deep in thought, large negative space with mountain mist, half light half shadow, introspective mood",

    # 副歌 Chorus1（S09-S11）
    "grand panoramic view of Yanqing Men martial arts school, majestic gates, pine trees lining square, plaque hanging high, main hall with flying eaves, sunset clouds, gold and jade green, magnificent",
    "hero standing with arms open facing magnificent rivers and mountains, vast land beneath, infinite sky, golden sunlight bathing scene, wide angle composition, epic sense",
    "fingertip flicking, silver sword energy blooming into semi-transparent ink-wash sword flower, petals from ink black to gold, radiating light, beautiful visual impact",

    # 间奏（S12）
    "deep night mountain peak, Milky Way like waterfall pouring down, starlight reflected in winding river, ancient pagoda silhouette, mountains like ink wash, fireflies, ethereal tranquil",

    # 女声 Verse3（S13-S14）
    "magnificent landscape, bright starry river reflected in surging river, layered mountain banks, vast sky and earth, river surface shimmering, deep night sky, cool blue-purple tones",
    "huge waves crashing against sea reef standing firm for thousands of years, spray flying like broken jade, distant mountains and dark blue night sky, power and eternity",

    # 男声 Verse4（S15）
    "yellowed ancient history book opened on desk, vertical ink characters, golden light rising like soul from pages, candlelight flickering, silhouettes of legendary warriors layered over pages, sacred solemn",

    # 副歌 Chorus2（S16-S18）
    "looking outward from inside Yanqing Gate, light and shadow at threshold, magnificent mountains and golden prosperous age outside, pine trees, sunset clouds, warm golden tones",
    "prosperous ancient capital city street, peaceful marketplace, shops with red lanterns, pedestrians chatting, children playing, golden sunset over city, warm prosperous scene",
    "silhouette of couple standing side by side at sunset, hair from black to silver white, poetic warm golden tones, romantic, large sunset contrasting with small figures",

    # 桥段（S19）
    "traditional Chinese courtyard houses, cooking smoke rising from roofs, children playing in yard, elderly sitting under tree smiling, warm autumn sunlight, peaceful harmony",

    # 尾声（S20-S21）
    "vast grassland, two riders galloping on horses toward distance, horses leaping, robes flying, golden sunset light flooding prairie, freedom and speed",
    "two riders silhouettes growing smaller on horizon, merging into huge golden setting sun, brilliant sunset clouds, rule of thirds, lingering mood, ending with vast emptiness",
]

# ============================================================
# 4. 批量生成（每张图加入音频情感修饰）
# ============================================================

total = len(scene_prompts)
start_time = time.time()

for i, prompt in enumerate(scene_prompts, 1):
    _, _, mood, tone = audio_features[i-1]

    # 合成 final prompt = 风格前缀 + 场景描述 + 色调 + 情绪
    mood_en = {"宁静":"serene quiet", "平缓":"calm gentle", "温暖":"warm emotional"}
    tone_en = {"暖色":"warm golden tones", "中性":"jade green neutral tones"}
    full_prompt = f"{STYLE_PREFIX}, {prompt}, {tone_en.get(tone, '')}, {mood_en.get(mood, '')}"

    generator = torch.Generator("cuda").manual_seed(MASTER_SEED + i)

    print(f"[{i:02d}/{total}] {mood}...")

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
