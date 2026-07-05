#!/bin/bash
# ============================================================
# 燕青门 Wan2.2 AutoDL 一键生成脚本
# RTX 5090 预计 ~1小时完成全部53段
# ============================================================

cd /root

GEN="python /root/Wan2.2/generate.py"
CKPT="--task ti2v-5B --size 1280*704 --ckpt_dir /root/Wan2.2-TI2V-5B-bf16 --offload_model True --t5_cpu --frame_num 121"
OUTDIR="/root/yanqingmen_output"
mkdir -p $OUTDIR $OUTDIR/raw

# ============================================================
# 21段分镜，每段2-3个镜头
# 格式: 目标时长(秒) | 镜头1 | 镜头2 | 镜头3
# ============================================================
SEGMENTS=(
  "13|秋日古城全景航拍，金色银杏覆青瓦，斑驳城墙蜿蜒如龙，远山云雾，暖金夕阳从城门透出|古城墙平视，青砖斑驳苔痕，墙头秋草摇曳，远处飞檐若隐若现|青石板路反射夕阳，红灯笼随风轻摆，落叶飘过，人影稀疏"
  "13|古城门仰拍特写，门钉铜绿，石狮威严，门缝透暖光，青松枝桠探墙头，秋叶落石阶|石狮头部特写，鬃毛纹理清晰，眼神威严，背景虚化城门|门缝透光近景，厚木门微开，暖光从缝隙照亮石阶，青苔蔓延"
  "12|老茶馆内景，白发说书人执折扇坐木椅，青瓷茶盏热气袅袅，竹影投纸窗|说书人面部特写，眼神深邃，折扇半遮面，烛光映皱纹|茶盏特写，青瓷茶汤微漾，热气升腾，背景虚化说书人剪影"
  "12|月洞门框景，翠竹摇曳，石径蜿蜒，燕青门匾额隐约可见，雨后青石倒映天光|青竹特写，叶沾雨滴，竹竿挺拔，背景虚化白墙|雨后石阶，水洼倒映天色，光影斑驳，空无人迹"
  "13|旧木案上泛黄经络图展开，银针草药半烛，窗外光照卷轴，暖褐暗红|经络图特写，墨线勾勒穴位，朱砂标注，烛光摇曳|石阶剑痕特写，深浅刻痕交错，青苔蔓延，阳光斜照"
  "13|大远景，白衣侠客立山巅，背对画面，云海翻腾，丁达尔金光斜射|群山层叠云海大景，侠客渺小剪影融入天地，壮阔|侠客侧身握剑，风吹发丝，眼神远眺，金色光勾勒轮廓"
  "10|侠客侧身拉弓如满月，箭离弦化作漫天粉白花瓣，暮色晚霞为背景|花瓣飞花全景，粉白花瓣旋舞如雪，侠客剪影立于花雨中"
  "13|侠客低首凝视长剑，剑身映眉眼，若有所思，留白背景流云|剑身特写，寒光凛冽映出侠客眼眸，剑刃纹理清晰|空镜流云掠过山巅，天地苍茫，何以为侠"
  "9|燕青门全景，青松列植，门匾高悬，主殿飞檐翘角，晚霞绚烂|门匾特写，燕青门三字苍劲，金漆斑驳，晚霞映照"
  "11|侠客张开双臂面向锦绣山河，金色阳光沐浴，广角构图，史诗感|山河全景俯拍，群山层叠河流蜿蜒，侠客渺小身影立于天地间"
  "11|指尖轻弹，银色剑气绽放成半透明水墨剑花，墨色到金色渐变|剑花绽放全景，光芒中侠客剪影，花瓣飞散"
  "15|璀璨银河横跨夜空，星光倒映江河，冷蓝深紫夜色，萤火几点|一人独坐古塔上仰望星空，背影孤独，情感锚点|江面倒映星空，波光粼粼，山峦如墨"
  "8|银河旋转延时感，星轨流动如瀑布，古塔剪影静立|山峦层叠如黛，夜色苍茫，河面银光"
  "9|惊涛拍岸卷千堆雪，礁石屹立浪中纹丝不动，远景山河辽阔|浪花特写，巨浪拍击礁石，水花飞溅如碎玉"
  "14|泛黄史书展开，竖排墨字，烛光摇曳，历代侠士剪影叠画|字迹特写，墨字苍劲，纸张泛黄，侠士剪影浮现|金色光芒从书页升腾如灵魂，神圣肃穆"
  "9|从燕青门内向外望，门槛光影交错，门外山河金辉盛世|门外山河全景，门框构图，晚霞漫天"
  "13|繁华古都街景，商铺林立，红灯笼连成星河，金色夕阳笼罩|街市中景，行人谈笑，孩童追逐，生活气息|灯笼特写，暖光映照，背景虚化人影"
  "11|夕阳下男女并肩剪影，头发由黑渐白，暖金色调温柔浪漫|落日余晖全景，二人渺小剪影，留白"
  "14|古风院落错落，炊烟袅袅，孩童追逐，秋日暖阳|孩童嬉戏近景，追逐欢笑，背景虚化院落|老人坐古树下含笑，鸡犬相闻"
  "14|草原天际线，双人策马奔腾，夕阳金光洒满草原|马蹄飞扬特写，马鬃飘动，速度张力|双人骑马侧拍，衣袂飞扬，自由豪迈"
  "14|双人骑马远去，背影融入巨大金色落日，三分法构图|远景晚霞漫天，二人剪影即将消失|空镜落日半沉，余晖渲染天际，天地宁静"
)

TOTAL=${#SEGMENTS[@]}

for i in "${!SEGMENTS[@]}"; do
  NUM=$(printf "%02d" $((i+1)))
  IFS='|' read -ra SHOTS <<< "${SEGMENTS[$i]}"

  TARGET_DUR="${SHOTS[0]}"
  PROMPTS=("${SHOTS[@]:1}")
  NUM_SHOTS=${#PROMPTS[@]}

  echo ""
  echo "=============================================="
  echo "分段 $NUM/$TOTAL (目标${TARGET_DUR}s, ${NUM_SHOTS}个镜头)"
  echo "=============================================="

  RAW_FILES=""

  for j in "${!PROMPTS[@]}"; do
    SHOT_NUM=$((j+1))
    PROMPT="${PROMPTS[$j]}"
    OUTFILE="$OUTDIR/raw/raw_${NUM}_${SHOT_NUM}.mp4"

    echo ""
    echo "── 镜头 $SHOT_NUM/$NUM_SHOTS ──"
    echo "Prompt: $PROMPT"

    # 自动续费，防止生成到一半实例过期
    autodl renew > /dev/null 2>&1 || true

    # 开始时间
    T0=$(date +%s)

    time $GEN $CKPT \
      --prompt "$PROMPT" \
      --save_file "$OUTFILE" \
      2>&1 | tail -3

    T1=$(date +%s)
    echo "  ✅ 镜头 $SHOT_NUM 完成 ($((T1-T0))秒)"

    RAW_FILES="$RAW_FILES $OUTFILE"
  done

  # 单镜头直接复制，多镜头用ffmpeg拼接
  echo ""
  echo "── 拼接 ${NUM_SHOTS}个镜头 → v${NUM}.mp4 ──"

  if [ "$NUM_SHOTS" -eq 1 ]; then
    cp "$OUTDIR/raw/raw_${NUM}_1.mp4" "$OUTDIR/v${NUM}.mp4"
  else
    # 创建concat列表
    LIST_FILE="$OUTDIR/raw/list_${NUM}.txt"
    rm -f "$LIST_FILE"
    for f in $RAW_FILES; do
      echo "file '$f'" >> "$LIST_FILE"
    done

    # 拼接
    ffmpeg -y -f concat -safe 0 -i "$LIST_FILE" \
      -c:v copy \
      "$OUTDIR/v${NUM}_merged.mp4" 2>/dev/null

    # 计算慢放因子
    RAW_DUR=$((NUM_SHOTS * 5))
    RATIO=$(echo "scale=2; $TARGET_DUR / $RAW_DUR" | bc)

    if [ "$(echo "$RATIO > 1.05" | bc)" -eq 1 ]; then
      NEW_FPS=$(echo "scale=0; 24 * $RATIO / 1" | bc)
      ffmpeg -y -i "$OUTDIR/v${NUM}_merged.mp4" \
        -vf "minterpolate=fps=$NEW_FPS:mi_mode=mci:mc_mode=aobmc" \
        -t "$TARGET_DUR" \
        -c:v libx264 -crf 18 -preset medium \
        "$OUTDIR/v${NUM}.mp4" 2>/dev/null
    else
      cp "$OUTDIR/v${NUM}_merged.mp4" "$OUTDIR/v${NUM}.mp4"
    fi

    rm -f "$OUTDIR/v${NUM}_merged.mp4"
  fi

  # 验证时长
  ACTUAL=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$OUTDIR/v${NUM}.mp4" 2>/dev/null)
  echo "  ✅ v${NUM}.mp4 → ${ACTUAL}s (目标${TARGET_DUR}s)"
done

echo ""
echo "=============================================="
echo "🎉 全部完成！共 $TOTAL 段视频"
echo "📁 $OUTDIR/v01.mp4 ~ v$(printf "%02d" $TOTAL).mp4"
echo "=============================================="
