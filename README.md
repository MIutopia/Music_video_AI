# Music_video_AI · 燕青门 AI 音乐 MV

> 从歌词到完整音乐 MV 的全流程开源方案

GitHub: `https://github.com/MIutopia/Music_video_AI`

## 项目简介

用免费 AI 工具，将《燕青门》歌词转化为完整的音乐 MV。全部在网页端完成素材生成，本地仅用 ffmpeg 合成，无需 GPU。

### 技术路线

```
歌词 → 网易天音 → 燕青门歌曲音频（4分22秒）
                            ↓
        通义万相图组 → 8张统一风格古风图
                            ↓
           即梦图生视频 → 每张图生成5秒动态视频
                            ↓
     ffmpeg minterpolate 智能慢放填满时长
                            ↓
           拼接 + 字幕 + 音频合成
                            ↓
                    🎬 最终 MV
```

### 硬件需求

| 项目 | 需求 |
|------|------|
| 本地显卡 | 仅 2GB VRAM ✅（只跑 ffmpeg） |
| 本地工具 | ffmpeg |
| 云端平台 | 通义万相（免费生图）、即梦（免费图生视频） |

## 使用流程

### 第1步：歌曲 ✅ 已完成

`audio/yanqingmen.wav` — 网易天音生成，4分22秒

### 第2步：通义万相图组生图 ⬅️ 下一步

打开 https://tongyi.aliyun.com/wanxiang/

1. 创建**图组**（不是单张生图）
2. 输入统一风格描述（见 `docs/prompts.md`）
3. 按 8 张图 Prompt 逐个生成
4. 下载图片

### 第3步：即梦图生视频

打开 https://jimeng.jianying.com

1. 选择**图生视频**
2. 上传通义万相生成的图片
3. 每张生成 1 段 5 秒视频
4. 下载视频放入 `videos/raw/p01.mp4` ~ `p08.mp4`

### 第4步：一键合成

双击 `scripts/build_all.bat`，自动完成：

```
原始视频（8段 × 5秒 = 40秒）
    ↓ minterpolate 运动补偿慢放
慢放后视频（≈ 260秒）
    ↓ concat 拼接
完整视频
    ↓ 字幕叠加（楷体，中英双语）
    ↓ 音频合成
🎬 output/yanqingmen_mv_final.mp4
```

如果慢放后视频仍不够长，脚本会自动循环画面填满整首歌。

## 项目结构

```
Music_video_AI/
├── audio/               # 歌曲音频（已完成）
│   └── yanqingmen.wav
├── videos/
│   ├── raw/             # 放入即梦生成的视频（p01.mp4 ~ p08.mp4）
│   ├── clips/           # 中间文件（自动生成）
│   └── slowmo/          # 慢放后文件（自动生成）
├── subs/
│   └── yanqingmen.srt    # 中英双语字幕
├── scripts/
│   └── build_all.bat     # 🚀 一键合成
├── docs/
│   └── prompts.md        # 通义万相图组 + 即梦图生视频 Prompt
├── output/               # 最终输出
└── README.md
```

## 历史版本

| 版本 | 方案 | 日期 |
|------|------|------|
| v1 | Kling文生视频 + ffmpeg合成 | 废弃 |
| v2 | 静态图片Ken Burns | 废弃 |
| v3 | 通义万相图组 + 即梦图生视频 + minterpolate慢放 | ✅ 当前 |
