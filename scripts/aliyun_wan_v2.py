# ============================================================
# Agnes AI Video V2.0 版本：22段视频生成
# 前奏26秒 + 歌词21段 = 262秒
# ============================================================

import requests, json, time, os
from math import ceil

# ============================================================
# 配置区
# ============================================================
API_KEY = "sk-bg4CsecmykgLffFq3BELWgiOxW63SsW05wmVwMm8thLM7Zp2"
BASE_URL = "https://apihub.agnes-ai.com"
OUT = r"C:\Users\MIutopia\Desktop\新建文件夹"
os.makedirs(OUT, exist_ok=True)

H = {
    "Authorization": "Bearer " + API_KEY,
    "Content-Type": "application/json"
}

# ============================================================
# 视频时长 → num_frames 转换函数
# Agnes AI 要求：num_frames ≤ 441，且遵循 8n+1 规则
# ============================================================
def seconds_to_frames(seconds, fps=24):
    """将秒数转换为符合 Agnes AI 要求的帧数（8n+1，≤441）"""
    target_frames = int(seconds * fps)
    # 确保 ≥ 9（最小的 8n+1 且 > 1）
    if target_frames < 9:
        target_frames = 9
    # 限制最大值 441
    if target_frames > 441:
        target_frames = 441
    # 调整为 8n+1
    adjusted = ((target_frames - 1) // 8) * 8 + 1
    return adjusted

def get_actual_seconds(num_frames, fps=24):
    """计算实际视频时长"""
    return num_frames / fps

# ============================================================
# 统一的风格锚点
# ============================================================
STYLE_BASE = "写实古风摄影，"
STYLE_COLOR = "主色调为冷青灰蓝，局部暖金色点缀，画面清透干净，饱和度适中不艳俗，"
STYLE_LIGHT = "自然侧逆光为主，柔和不生硬，有丁达尔光效，暗部保留细节不欠曝，高光不过曝，"
STYLE_TEXTURE = "电影级画质，纹理细节清晰，人物肤质真实，景深层次分明，16比9宽幅，"
CHARACTER_YANQING = "浪子燕青形象，面容俊朗清秀，束发高髻，额前两缕碎发，身形矫健挺拔，气质潇洒不羁中带书卷气，白衣青衫为主，腰间常挂竹箫，"
STYLE_FIX = "冷青暖金双色对比，胶片质感，意境留白"

def make_prompt(desc, has_character=False):
    char_part = CHARACTER_YANQING if has_character else ""
    return (STYLE_BASE + STYLE_COLOR + STYLE_LIGHT + STYLE_TEXTURE + 
            desc + char_part + STYLE_FIX)

# ============================================================
# 22段分镜 (S00-S22)
# 每段: (目标秒数, prompt, 是否含人物)
# ============================================================
SEGMENTS = [
    # S00-S01: 前奏 (13+13=26s)
    (13, make_prompt("晨雾中燕青门建筑群航拍全景，群山环抱云雾缭绕，飞檐翘角从雾中渐显，门匾在晨光中逐渐清晰，冷灰蓝调渐变暖金，宁静悠远"), False),
    (13, make_prompt("阳光刺破云层照亮青石台阶，镜头穿过门廊进入庭院，青松翠柏晨露未干，万物苏醒，暖金初升光线洒满庭院，生机盎然"), False),

    # S02-S05: 古城环境 (13+13+11+11=48s)
    (13, make_prompt("秋日古城航拍大远景，金色银杏覆盖青瓦屋顶，古城墙蜿蜒如龙，暖金色夕阳从城门洞透出照亮青石板路，整座城沉睡在时光里"), False),
    (13, make_prompt("老茶馆内景，白发苍苍的说书人坐于木案后手执折扇，青瓷茶盏冒着热气，窗外竹影投在纸窗上，暖黄烛光摇曳，叙事感"), False),
    (11, make_prompt("幽深庭院月洞门框景，青砖灰瓦，门楣斑驳匾额，青竹探出院墙，石灯笼爬青苔，雨后青石倒映天光，黄叶飘落"), False),
    (11, make_prompt("燕青门匾额木质特写，刻字苍劲有力，横移镜头扫过堂内旧弓、褪色锦旗、木人桩、兵器架，光影中尘埃浮游，岁月包浆感"), False),

    # S06-S09: 剑与医 + 燕青出场 (12+12+12+12=48s)
    (12, make_prompt("古剑横陈极特写微距，剑身密布细密磨痕，雨滴从屋檐落下砸在剑脊溅开水花，水流顺剑身蜿蜒如泪，剑槽积水映天光"), False),
    (12, make_prompt("旧木案上泛黄经络图卷轴展开，朱砂标注穴位，银针排列如阵，石臼草药半研，残烛火苗微摇，天光斜照尘埃飞舞"), False),
    (12, make_prompt("白衣侠客立于山巅巨岩背对画面，长袍在狂风中猎猎翻飞，前方云海翻腾，金色夕阳透出丁达尔光柱，背影孤绝如丰碑"), True),
    (12, make_prompt("白衣侠客侧身站立手扶腰间竹箫，风拂动发丝衣袂，侧首远望目光深邃，嘴角含笑，潇洒中带书卷气"), True),

    # S10-S14: 燕青射箭与问道 (11+10+10+10+11=52s)
    (11, make_prompt("燕青侧身站立左手持川弩右手拉弦，弓如满月身姿挺拔如松，眼神锐利锁定前方，背景苍茫暮色远山"), True),
    (10, make_prompt("箭矢离弦刹那爆出漫天粉白花瓣，梨花海棠杏花纷扬如暴雪，花瓣旋舞成花之轨迹，燕青收弓花瓣落肩头"), True),
    (10, make_prompt("燕青收弓转身，被救百姓感恩，孩童扑向父母，老翁含泪作揖，远处城郭夕阳金辉，燕青淡然一笑"), True),
    (10, make_prompt("燕青低头凝视手中长剑，剑身寒光映出眉眼，抬头望向远方，背景大面积留白山水流云，光影半明半暗"), True),
    (11, make_prompt("燕青立于万山之巅展臂如鹰翼，衣袂翻飞，脚下群山江河天地辽阔，闭目倾听，风中似有历代回响"), True),

    # S15-S18: 俯瞰与传承 (12+15+7+8=42s)
    (12, make_prompt("镜头极速从燕青身上抽离穿过云层俯瞰山河，山河如棋盘城池如星点，小小人影站山顶渺小坚定，字幕浮现何以为侠"), True),
    (15, make_prompt("燕青门建筑群全景仰拍，门匾金光闪耀飞檐翘角层叠，门前树叶嫩绿金黄凋零新芽四季流转，晚霞绚烂"), False),
    (7, make_prompt("燕青门弟子庭院中练武，右手持剑手腕旋转划出螺旋圆弧，剑光如银白衣如云，动作行云流水"), True),
    (8, make_prompt("燕青射敌寇、施针治病、护旗城楼、抚孩童微笑，四组动作快速连续切换，统一暖金色调"), True),

    # S19-S22: 盛世与尾声 (8+11+12+14=45s)
    (8, make_prompt("燕青站城门前右手弹指剑花，剑花如涟漪荡开，身后废墟变繁华，残垣生花人群重现红灯笼亮起"), True),
    (11, make_prompt("夕阳下燕青与女子并肩剪影站城墙之上面朝落日，两人头发从乌黑渐变为银白，暖金落日大面积留白"), True),
    (12, make_prompt("古风院落群全景，屋顶炊烟袅袅升入暖空，孩童追跑嬉闹，老人古树下喝茶，年轻人练武场挥汗，盛世安宁"), False),
    (14, make_prompt("草原天际线大远景，夕阳金光洒满草原，双人策马奔向远方融入金色落日，画面最后定格两人剪影与落日重合，漫天暖色晚霞，余韵悠长"), True),
]

# ============================================================
# 计算总时长并转换为帧数
# ============================================================
FPS = 24
total_seconds = sum(s[0] for s in SEGMENTS)
print(f"📊 共 {len(SEGMENTS)} 段，目标总时长: {total_seconds}s")

# 生成每段的任务参数
tasks_params = []
for i, (sec, prompt, has_char) in enumerate(SEGMENTS):
    num_frames = seconds_to_frames(sec, FPS)
    actual_sec = get_actual_seconds(num_frames, FPS)
    tasks_params.append({
        "index": i,
        "target_sec": sec,
        "num_frames": num_frames,
        "actual_sec": actual_sec,
        "prompt": prompt,
        "has_character": has_char
    })
    print(f"  S{i:02d}: {sec}s → {num_frames}帧 ({actual_sec:.2f}s)")

# ============================================================
# 提交任务到 Agnes AI
# ============================================================
print(f"\n=== 提交 {len(tasks_params)} 段到 Agnes AI ===")

task_ids = []  # 存储 (index, video_id, task_id)
for p in tasks_params:
    idx = p["index"]
    body = {
        "model": "agnes-video-v2.0",
        "prompt": p["prompt"],
        "num_frames": p["num_frames"],
        "frame_rate": FPS,
        "height": 768,
        "width": 1152,  # 16:9
        "negative_prompt": "模糊, 变形, 色彩失真, 过度曝光, 低画质, 不自然的人脸, 扭曲的身体比例"
    }
    
    print(f"  [S{idx:02d}] 提交中 ({p['actual_sec']:.1f}s, {p['num_frames']}帧)...", end=" ")
    
    for retry in range(3):
        try:
            r = requests.post(
                BASE_URL + "/v1/videos",
                headers=H,
                json=body,
                timeout=120
            )
            if r.status_code == 200:
                data = r.json()
                video_id = data.get("video_id")
                task_id = data.get("task_id") or data.get("id")
                if video_id:
                    task_ids.append((idx, video_id, task_id, p["actual_sec"]))
                    print(f"✅ video_id: {video_id}")
                    break
                else:
                    print(f"⚠️ 无video_id: {data}")
            else:
                print(f"❌ HTTP {r.status_code}: {r.text[:200]}")
        except Exception as e:
            print(f"❌ 异常: {e}")
            if retry < 2:
                time.sleep(5)
    time.sleep(2)

print(f"\n✅ 成功提交 {len(task_ids)}/{len(tasks_params)} 个任务")

# ============================================================
# 轮询获取结果
# ============================================================
print(f"\n=== 轮询获取视频 ===")

pending = task_ids[:]
results = {}
while pending:
    for item in pending[:]:
        idx, video_id, task_id, actual_sec = item
        try:
            r = requests.get(
                BASE_URL + "/agnesapi",
                params={"video_id": video_id},
                headers={"Authorization": "Bearer " + API_KEY},
                timeout=60
            )
            if r.status_code == 200:
                data = r.json()
                status = data.get("status")
                progress = data.get("progress", 0)
                
                if status == "completed":
                    video_url = data.get("remixed_from_video_id")
                    if video_url:
                        # 下载视频
                        print(f"  [S{idx:02d}] 下载中...", end=" ")
                        vd = requests.get(video_url, timeout=120).content
                        with open(os.path.join(OUT, f"S{idx:02d}.mp4"), "wb") as f:
                            f.write(vd)
                        print(f"✅ ({len(vd)//1024}KB)")
                        results[idx] = True
                        pending.remove(item)
                    else:
                        print(f"  [S{idx:02d}] ⚠️ completed但无视频URL")
                        pending.remove(item)
                elif status == "failed":
                    error = data.get("error", "未知错误")
                    print(f"  [S{idx:02d}] ❌ 失败: {error}")
                    pending.remove(item)
                else:
                    # queued / in_progress
                    print(f"  [S{idx:02d}] ⏳ {status} ({progress}%)")
            else:
                print(f"  [S{idx:02d}] ⚠️ HTTP {r.status_code}")
        except Exception as e:
            print(f"  [S{idx:02d}] ⚠️ 轮询异常: {e}")
    
    if pending:
        print(f"  . 剩余 {len(pending)} 个任务，等待15秒...")
        time.sleep(15)

# ============================================================
# 完成
# ============================================================
print(f"\n🎬 完成！成功生成 {len(results)}/{len(tasks_params)} 段")
print(f"📁 文件: {OUT}\\S00.mp4 ~ S{len(tasks_params)-1:02d}.mp4")
print(f"📊 总时长: {total_seconds}s (约 {total_seconds/60:.1f} 分钟)")