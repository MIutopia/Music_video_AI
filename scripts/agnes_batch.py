# ============================================================
# Agnes AI 批量视频生成 · 优化版
# 支持：多账号轮询 / 风格统一 / 断点续传 / 限流处理
# ============================================================

import urllib.request, json, time, os, sys

# ============================================================
# 配置区
# ============================================================

# 多个 API Key 轮流用（突破每日500秒限制）
API_KEYS = [
    "sk-4jVrrvrbe7Mu2Lrh0GGBFUXtrb9alAUrC0M31xERD7cPin9j",   # 账号1
    "sk-bg4CsecmykgLffFq3BELWgiOxW63SsW05wmVwMm8thLM7Zp2",    # 账号2（新）
]

# 输出目录
OUTPUT = "C:\\Users\\MIutopia\\Desktop\\yanqingmen_videos"

# 每段目标时长（秒）
DURATIONS = [13,13,12,12,13,13,13,14,12,11,11,15,8,9,14,12,13,12,14,14,14]

# ============================================================
# 统一风格前缀（确保所有视频画面风格一致）
# ============================================================
STYLE_PREFIX = "古风水墨画，青绿山水与水墨淡彩结合，色彩雅致留白，诗意光影，电影感构图，16:9，"

PROMPTS = [
    "秋日古城全景航拍，金色银杏覆青瓦，城墙蜿蜒如龙，远山云雾缭绕，暖金夕阳从城门透出，宁静悠远",
    "古城门仰拍，门钉铜绿斑驳，石狮威严肃穆，门缝透出暖光，青松探出墙头，秋叶飘落石阶，古朴庄重",
    "老茶馆内景，白发说书人执折扇坐木椅，青瓷茶盏热气袅袅，窗外竹影投纸窗，暖黄烛光，叙事感",
    "幽深庭院月洞门，燕青门匾额隐约可见，青竹探墙，石灯青苔，雨后青石倒映天光，青绿主调",
    "旧木案泛黄经络图卷轴展开，银针草药半烛，窗外天光照卷轴，暖褐暗红调，古朴神秘",
    "白衣侠客立山巅巨岩，背对画面，长袍劲风翻飞，腰佩古剑，云海翻腾，丁达尔金光斜射，壮阔豪情",
    "侠客侧身拉弓如满月，箭矢离弦化作漫天粉白花瓣旋舞，暮色远山晚霞，浪漫与力量",
    "侠客低首凝视长剑，剑身映出眉眼，若有所思，背景留白山色流云，光影半明半暗，深沉内省",
    "燕青门宏伟建筑群全景，广场青松列植，门匾高悬，飞檐翘角，晚霞绚烂，金色青绿交织，恢弘壮丽",
    "侠客立天地间张开双臂面向锦绣山河，脚下大地辽阔，苍穹无垠，金色阳光沐浴全身，史诗感",
    "指尖轻弹，银色剑气绽放成水墨剑花，墨色到金色渐变，光芒四射，极致唯美，慢动作特写",
    "璀璨银河横跨夜空，星光倒映蜿蜒江河，古塔剪影，山峦如墨，冷蓝深紫夜色，空灵静谧",
    "银河缓缓旋转流动如瀑布倾泻，古塔剪影静立，星轨流动，冷蓝紫色调，时间流逝感",
    "惊涛拍岸卷千堆雪，巨大礁石屹立浪中纹丝不动，浪花飞溅如碎玉，力量感与永恒感，慢动作",
    "泛黄史书缓缓翻开，竖排墨字苍劲，侠士剪影叠画浮现，金色光芒从书页升腾，烛光摇曳，神圣肃穆",
    "从燕青门内向外望，门槛内外光影交错，门外壮丽山河金辉盛世，温暖金色调，传承与希望",
    "繁华古都街景，商铺林立，红灯笼暖光连成星河，行人谈笑孩童追逐，金色夕阳笼罩全城，太平景象",
    "夕阳下男女二人并肩剪影，头发由黑渐银白，暖金色调温柔浪漫，落日余晖与人影对比，岁月静好",
    "古风院落错落，炊烟袅袅升腾，孩童嬉戏追逐，老人古树下含笑，秋日暖阳洒满庭院，祥和安宁",
    "壮阔草原天际线，双人策马奔腾，骏马腾空衣袂飞扬，夕阳金黄洒满草原，自由豪迈",
    "双人骑马远去背影越来越小，融入巨大金色落日，漫天暖色晚霞，留白意蕴悠长，结尾余韵",
]

assert len(DURATIONS) == len(PROMPTS), "时长和Prompt数量不一致"

# ============================================================
# 工具函数
# ============================================================

def api_post(key, body):
    """提交视频任务"""
    h = {"Authorization": "Bearer " + key, "Content-Type": "application/json"}
    req = urllib.request.Request(
        "https://apihub.agnes-ai.com/v1/videos",
        data=json.dumps(body).encode(), headers=h, method="POST"
    )
    resp = json.loads(urllib.request.urlopen(req, timeout=60).read())
    return resp

def api_poll(key, video_id):
    """查询视频状态"""
    h = {"Authorization": "Bearer " + key}
    req = urllib.request.Request(
        f"https://apihub.agnes-ai.com/v1/videos/{video_id}",
        headers=h, method="GET"
    )
    resp = json.loads(urllib.request.urlopen(req, timeout=30).read())
    return resp

def submit_with_retry(key, body, max_retries=10):
    """带限流重试的提交"""
    for attempt in range(max_retries):
        try:
            resp = api_post(key, body)
            vid = resp.get("id") or resp.get("video_id")
            if vid:
                return vid
            # 检查是否限流
            err = resp.get("error", {}).get("message", "")
            if "rate_limit" in err.lower():
                wait = 60 + attempt * 10
                print(f"    限流, 等待{wait}秒...")
                time.sleep(wait)
                continue
            print(f"    返回异常: {resp}")
            return None
        except Exception as e:
            s = str(e)
            if "429" in s or "rate" in s.lower():
                wait = 60 + attempt * 10
                print(f"    限流({s[:30]}), 等待{wait}秒...")
                time.sleep(wait)
                continue
            print(f"    错误: {s[:60]}")
            time.sleep(30)
            return None
    return None

# ============================================================
# 主流程
# ============================================================

os.makedirs(OUTPUT, exist_ok=True)

# 记录已完成的任务（断点续传）
done = set()
for f in os.listdir(OUTPUT):
    if f.endswith(".mp4") and f.startswith("p"):
        idx = int(f[1:3])
        done.add(idx)

print(f"已有 {len(done)} 个视频完成，剩余 {21-len(done)} 个")

key_idx = 0
total_submitted = 0
pending = []  # [(索引, video_id, 时长, key)]

for i in range(21):
    if (i + 1) in done:
        print(f"[{i+1:02d}/21] 已存在，跳过")
        continue

    key = API_KEYS[key_idx % len(API_KEYS)]
    dur = DURATIONS[i]
    # num_frames 必须是 4n+1，时长×24帧≈总帧数
    frames = ((dur * 24) // 4) * 4 + 1
    prompt = STYLE_PREFIX + PROMPTS[i]

    print(f"[{i+1:02d}/21] 提交 ({dur}s, {frames}帧, 账号{key_idx % len(API_KEYS)+1})...")
    print(f"  Prompt: {prompt[:50]}...")

    body = {
        "model": "agnes-video-v2.0",
        "prompt": prompt,
        "width": 1152,
        "height": 768,
        "num_frames": frames,
        "frame_rate": 24,
    }

    vid = submit_with_retry(key, body)
    if vid:
        pending.append((i + 1, vid, dur, key))
        total_submitted += 1
        print(f"  ✅ 任务ID: {vid}")
    else:
        print(f"  ❌ 提交失败")

    # 每提交一个后切换账号+等70秒避免限流
    key_idx += 1
    if i < 20:  # 最后一段不用等
        print(f"  等待70秒（限流保护）...")
        time.sleep(70)

print(f"\n提交完成: {total_submitted}个任务等待产出的")
print(f"开始轮询...")

# ============================================================
# 轮询结果
# ============================================================
while pending:
    for item in pending[:]:
        i, vid, dur, key = item
        try:
            resp = api_poll(key, vid)
            status = resp.get("status", "")
            if status == "succeeded":
                # 获取下载URL
                data_list = resp.get("data", [])
                if data_list:
                    url = data_list[0].get("url", "")
                    if url:
                        video_data = urllib.request.urlopen(url, timeout=60).read()
                        path = os.path.join(OUTPUT, f"p{i:02d}.mp4")
                        with open(path, "wb") as f:
                            f.write(video_data)
                        print(f"  ✅ p{i:02d}.mp4 ({dur}s, {len(video_data)//1024}KB)")
                        pending.remove(item)
            elif status in ("failed", "error", "cancelled"):
                print(f"  ❌ p{i:02d} 失败: {resp.get('error', status)}")
                pending.remove(item)
        except Exception as e:
            pass  # 下次再试

    if pending:
        print(f"  等待中...剩余{len(pending)}个")
        time.sleep(20)

print(f"\n{'='*50}")
print(f"🎉 全部完成！共 {total_submitted} 段视频")
print(f"📁 输出: {OUTPUT}")
print(f"{'='*50}")
