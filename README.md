# Music_video_AI · 燕青门 AI 音乐 MV

> 从歌词到完整音乐 MV 的全流程开源方案

GitHub: `https://github.com/MIutopia/Music_video_AI`

## 项目简介

用免费开源 AI 工具，将《燕青门》歌词转化为完整的音乐 MV。

### 技术路线

```
歌词 → Suno / ACE-Step → 歌曲音频
                         ↓
                  可灵 Kling → 12段古风视频片段
                         ↓
                  ffmpeg 合成 → 调色 + 转场 + 字幕 + 音频
                         ↓
                  最终 MV 输出
```

### 硬件需求

| 项目 | 需求 |
|------|------|
| 本地显卡 | 仅 2GB VRAM（够用） |
| 本地工具 | ffmpeg |
| 云端平台 | ACE-Step（acemusic.ai 免费）、可灵 Kling（免费额度） |

## 项目结构

```
yanqingmen-mv/
├── audio/              # 歌曲音频文件（通过 Suno/ACE-Step 生成）
│   └── yanqingmen.wav
├── videos/             # 视频素材
│   ├── raw/            # 从 Kling 下载的原始视频
│   └── processed/      # 标准化调色后的视频
├── subs/               # 字幕文件
│   ├── yanqingmen.srt  # 中英双语字幕
│   └── style.ass       # 字幕样式
├── scripts/            # 批处理脚本
│   ├── 01_normalize.bat  # 标准化+调色
│   ├── 02_merge.bat      # 视频拼接
│   └── 03_finalize.bat   # 最终合成
├── docs/
│   └── prompts.md      # Kling 提示词清单
├── output/             # 最终输出
├── .gitignore
└── README.md
```

## 使用流程

```bash
# 1. 生成歌曲音频 → 放入 audio/yanqingmen.wav
# 2. 从 Kling 下载视频 → 放入 videos/raw/
# 3. 按歌词调整 subs/yanqingmen.srt 的时间轴
# 4. 运行一键合成
cd scripts
build_all.bat
```

## 歌词

燕青门 · 古风武侠 · 男女对唱

歌词及英译详见 `docs/lyrics.md`。

## 许可证

MIT
