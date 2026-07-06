# ============================================================
# 阿里云 Wan2.7 批量文生视频
# 41段，与 prompts.md 精确对齐
# ============================================================

import requests, json, time, os

KEY = "sk-ws-H.EMMXIIY.8oC2.MEUCIFreghVF_6z1KnJslM-ciGsiLymz2o6VIyxfwhk1GWhtAiEAux1feokP2KUhBEnZK5pY6mxkGLU_Son_xvXRWsmcHJM"
BASE = "https://ws-l92l9bq2h6q5pd2d.cn-beijing.maas.aliyuncs.com/api/v1"
OUT = os.path.expanduser("~/Desktop/yanqingmen_videos")
os.makedirs(OUT, exist_ok=True)

H = {
    "Authorization": "Bearer " + KEY,
    "Content-Type": "application/json",
    "X-DashScope-Async": "enable"
}

STYLE = "古风水墨画，青绿山水淡彩色调，清透留白，光影柔和，电影级画质，"

PROMPTS = [
    STYLE + "秋日古城航拍大远景，金色银杏覆青瓦，城墙蜿蜒如龙，远山云雾缭绕，暖金夕阳从城门透出，宁静悠远，留白构图",
    STYLE + "古城墙中景横移，斑驳青砖布满苔痕，墙头秋草随风摇曳，远处古楼飞檐若隐若现，柔和散射光，岁月沧桑",
    STYLE + "古城门仰拍特写，门钉铜绿斑驳，石狮威严肃穆，门缝透出暖光，青松枝桠从墙头探出，秋叶飘落",
    STYLE + "石狮头部特写横移，鬃毛纹理清晰，目光威严凝视前方，秋叶缓缓飘过镜头，背景虚化城门，庄重肃穆",
    STYLE + "老茶馆内景，白发说书人坐木案后执折扇，青瓷茶盏热气袅袅，窗外竹影投纸窗，暖黄烛光充满画面，叙事感",
    STYLE + "茶盏特写俯拍，青瓷中茶汤微漾，白气袅袅升腾飘散，竹影在纸窗上晃动，背景虚化说书人剪影，宁静安逸",
    STYLE + "幽深庭院月洞门框景，门楣隐约可见燕青门匾额，青竹几竿探出院墙，石灯青苔，雨后青石倒映天光，青绿主调",
    STYLE + "雨后青石路向前延伸，青砖缝中细草新生，水面倒映天光，布鞋踏过泛起涟漪，光影斑驳，渐入幽深处",
    STYLE + "旧木案上泛黄经络图卷轴展开，银针排列，石臼草药半截残烛，窗外天光斜照案上，暖褐暗红调，古朴神秘",
    STYLE + "青石台阶剑痕特写，深浅刻痕交错如岁月刻印，石缝青苔蔓生，雨水沿剑痕缓缓流下，沧桑沉淀感",
    STYLE + "白衣侠客立于山巅巨岩背对画面，长袍在狂风中猎猎翻飞，前方云海翻腾，金色丁达尔光斜射，壮阔孤绝",
    STYLE + "侠客侧身中景，风吹发丝飞扬手按剑柄缓缓转身，金色侧逆光勾勒面部轮廓，目光坚毅望向远方，气势渐起",
    STYLE + "侠客侧身拉弓如满月，弓身紧绷弓弦震颤，箭尖寒光一点，衣袂鼓荡，暮色远山晚霞为背景，张力爆发前",
    STYLE + "箭矢离弦在空中化作漫天粉白花瓣炸开旋舞如暴雪，绚烂晚霞为背景，慢动作，花瓣漫天，浪漫与力量并存",
    STYLE + "侠客低首凝视长剑，剑身寒光映出眉眼，立领被风微拂面颊，背景留白山色流云缓慢变幻，半明半暗，沉思内省",
    STYLE + "剑身特写，剑刃纹理清晰，寒光凛冽中倒映出侠客眼眸，目光深邃若有所思，镜头缓慢推近，强化沉思氛围",
    STYLE + "燕青门宏伟建筑群全景仰拍，门匾高悬金光闪耀，主殿飞檐翘角层叠，天际晚霞绚烂如火，金色青绿交织，恢弘壮丽",
    STYLE + "门匾特写仰拍，燕青门三字苍劲有力金漆斑驳，檐角铜铃静悬，晚霞映照匾额金光闪烁，庄严厚重传承感",
    STYLE + "侠客立于万山之巅张开双臂面向锦绣山河，衣袂在风中展开如翼，脚下大地辽阔苍穹无垠，金色阳光沐浴全身，史诗感",
    STYLE + "山河全景高空俯瞰，层叠山峦云雾缭绕，江河蜿蜒如银练，侠客渺小身影立于山巅，天地辽阔人如芥子",
    STYLE + "手部特写，指尖轻弹动作优雅，一道银色剑气从指尖激射而出，在半空凝聚成形，光芒初现",
    STYLE + "水墨剑花在半空缓缓绽放盛开，花瓣由墨黑色渐变为璀璨金色，光芒四射照亮画面，花瓣飞散，极致唯美",
    STYLE + "璀璨银河横跨深蓝夜空，繁星密布如瀑布倾泻，冷蓝深紫夜色，画面深邃宁静，浩瀚宇宙感",
    STYLE + "古塔剪影孤立山巅之上，轮廓清晰，几点萤火缓缓飘飞闪烁，背景银河璀璨，孤独幽静遗世独立",
    STYLE + "平静江面特写，满天繁星倒映水中，水波微漾星光碎成片片光点，水天一色，空灵静谧",
    STYLE + "银河缓缓旋转流动如瀑布倾泻，星轨拖出弧线，古塔剪影静立不动，山峦层叠如黛，冷蓝紫色调，时间流逝感",
    STYLE + "惊涛骇浪猛烈拍击巨大黑色礁石，浪花炸开千堆雪，水花飞溅如碎玉崩裂，远景壮丽山河与暗蓝夜空，力量感永恒感",
    STYLE + "泛黄史书在木案上缓缓翻开，纸页边缘卷曲，竖排墨字工整苍劲，两侧烛火摇曳暖光照亮书页，厚重历史感",
    STYLE + "书页特写，墨字清晰有力，金色光芒从纸面缓缓渗出升腾如灵魂，烛光闪烁明暗交替，神圣肃穆",
    STYLE + "从燕青门内向外望的主观视角，门框形成天然画框，门槛内外明暗强烈对比，门外金光灿烂山河开阔",
    STYLE + "门外山河全景，青山耸立晚霞漫天铺展，温暖金色调阳光普照，青松苍劲挺拔，开阔希望传承感",
    STYLE + "繁华古都街市全景，商铺鳞次栉比，红灯笼连成星河，人流如织，金色夕阳笼罩全城，繁荣昌盛太平景象",
    STYLE + "红灯笼特写仰拍，暖光透过红绸洒落照亮下方行人孩童，灯穗轻摆，背景虚化为暖色光斑，温馨团圆感",
    STYLE + "夕阳下男女二人并肩立着的剪影，立领长衣随风微动，头发由乌黑渐变为银白，暖金色调，诗意浪漫",
    STYLE + "落日余晖大远景，巨大金色落日即将没入地平线，二人依偎剪影融入漫天晚霞，大面积留白，岁月静好",
    STYLE + "古风院落群全景，屋顶错落炊烟袅袅升入暖空，孩童院中追跑，秋日斜阳洒满瓦面，祥和安宁盛世家园",
    STYLE + "老人坐古树下藤椅上缓缓品茶，含笑看着孩童玩耍，鸡犬在脚边安卧，树影斑驳洒落，岁月安然知足",
    STYLE + "壮阔草原天际线大远景，双人策马奔腾向远方，夕阳金光洒满草原，骏马腾空衣袂飞扬，自由豪迈速度感",
    STYLE + "马蹄飞扬特写慢动作，马蹄腾空交错，尘土被夕阳照成金色，马鬃飘动肌肉线条充满力量美感",
    STYLE + "双人骑马远去中景背影，在夕阳余晖中奔向地平线，衣袂飘动光影温暖包裹，渐行渐远三分法构图",
    STYLE + "空镜，金色落日半沉地平线，漫天暖色绚烂晚霞，天地宁静空无一人，留白余韵悠长，全片终",
]

# 模型分布：同段内用同模型，41段正好
MODELS = (
    ["wan2.7-t2v"] * 2 +            # S01
    ["wan2.7-t2v-2026-06-12"] * 2 + # S02
    ["wan2.7-t2v"] * 2 +            # S03
    ["wan2.7-t2v-2026-04-25"] * 2 + # S04
    ["wan2.7-t2v"] * 2 +            # S05
    ["wan2.6-t2v"] * 2 +            # S06
    ["wan2.7-t2v"] * 2 +            # S07
    ["wan2.7-t2v-2026-06-12"] * 2 + # S08
    ["wan2.7-t2v"] * 2 +            # S09
    ["wan2.7-t2v-2026-04-25"] * 2 + # S10
    ["wan2.7-t2v"] * 2 +            # S11
    ["wan2.7-t2v-2026-06-12"] * 3 + # S12
    ["wan2.7-t2v"] * 1 +            # S13
    ["wan2.6-t2v"] * 1 +            # S14
    ["wan2.7-t2v"] * 2 +            # S15
    ["wan2.7-t2v-2026-06-12"] * 2 + # S16
    ["wan2.7-t2v"] * 2 +            # S17
    ["wan2.7-t2v-2026-04-25"] * 2 + # S18
    ["wan2.7-t2v"] * 2 +            # S19
    ["wan2.6-t2v"] * 2 +            # S20
    ["wan2.7-t2v"] * 2              # S21
)

assert len(MODELS) == len(PROMPTS), f"模型{len(MODELS)} ≠ Prompt{len(PROMPTS)}"
print(f"✅ {len(PROMPTS)} 段，模型与 prompts.md 对齐")

# ============================================================
# 提交 + 轮询
# ============================================================
print(f"\n=== 提交 {len(PROMPTS)} 个 ===")
tasks = []

for i in range(len(PROMPTS)):
    cn = i + 1
    body = json.dumps({
        "model": MODELS[i],
        "input": {"prompt": PROMPTS[i]},
        "parameters": {"duration": 5, "size": "1280*720"}
    }).encode()
    for retry in range(3):
        try:
            r = requests.post(BASE + "/services/aigc/videogeneration/text-to-video",
                data=body, headers=H, timeout=60).json()
            tid = r.get("output", {}).get("task_id")
            if tid:
                tasks.append((cn, tid, MODELS[i]))
                print(f"  [{cn:02d}/41] ✅")
                break
        except Exception as e:
            if retry < 2: time.sleep(10)
            else: print(f"  [{cn:02d}] {str(e)[:40]}")
    time.sleep(3)

print(f"\n提交 {len(tasks)} 个")

print("\n=== 轮询 ===")
pending = tasks[:]
while pending:
    for cn, tid, _ in pending[:]:
        try:
            r = requests.get(BASE + "/tasks/" + tid,
                headers={"Authorization": "Bearer " + KEY}).json()
            st = r.get("output", {}).get("task_status")
            if st == "SUCCEEDED":
                url = r.get("output", {}).get("video_url")
                if url:
                    d = requests.get(url, timeout=120).content
                    with open(os.path.join(OUT, f"p{cn:02d}.mp4"), "wb") as f:
                        f.write(d)
                    print(f"  ✅ p{cn:02d}.mp4 ({len(d)//1024}KB)")
                pending.remove((cn, tid, _))
            elif st == "FAILED":
                print(f"  ❌ p{cn:02d} 失败")
                pending.remove((cn, tid, _))
        except: pass
    if pending:
        print(f"  . 剩{len(pending)}个", end="", flush=True)
        time.sleep(15)

print(f"\n🎉 完成！{len(tasks)} 段")
print(f"📁 {OUT}")
print(f"💡 然后运行: python scripts/build_mv.py")
