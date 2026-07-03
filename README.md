# Music_video_AI · 燕青门 AI 音乐 MV

> 从歌词到完整音乐 MV 的全流程开源方案

GitHub: `https://github.com/MIutopia/Music_video_AI`

## 项目简介

用免费 AI 工具，将《燕青门》歌词转化为完整的音乐 MV。全部在网页端生成素材，本地仅用 ffmpeg 合成，无需 GPU。

### 技术路线

```
歌词 → 网易天音 → 歌曲音频（4分22秒）
                       ↓
    即梦/通义万相 → 古风国风图片（30+张）
                       ↓
    ffmpeg Ken Burns → 每张图片缓慢推拉平移（7-9秒/张）
                       ↓
    ffmpeg 拼接 + 转场 + 中英文字幕 + 歌曲音频
                       ↓
                 🎬 最终 MV 输出
```

### 硬件需求

| 项目 | 需求 |
|------|------|
| 本地显卡 | 仅 2GB VRAM ✅（只跑 ffmpeg） |
| 本地工具 | ffmpeg |
| 云端平台 | 即梦/通义万相（免费生图）、网易天音（免费作曲） |

## 项目结构

```
Music_video_AI/
├── audio/               # 歌曲音频（网易天音生成）
│   ├── yanqingmen.mp3   # 320kbps MP3
│   └── yanqingmen.wav   # WAV 无损（供合成用）
├── videos/
│   ├── raw/             # 放入即梦/通义万相生成的古风图片（p01.jpg ~ p33.jpg）
│   └── clips/           # Ken Burns 动画中间文件（自动生成）
├── subs/
│   └── yanqingmen.srt    # 中英双语字幕
├── scripts/
│   └── build_all.bat     # 🚀 一键合成脚本
├── docs/
│   └── prompts.md        # 30+ 张古风图片 Prompt 清单
├── output/               # 最终 MV 输出
└── README.md
```

## 使用流程

```text
1. 生成歌曲 → 已就绪！audio/yanqingmen.wav（4分22秒）
2. 生成图片 → 打开即梦，按 docs/prompts.md 生成30张古风图
3. 图片放入 → videos/raw/，命名为 p01.jpg ~ p33.jpg
4. 一键合成 → 双击 scripts/build_all.bat
5. 坐等出片 → output/yanqingmen_mv_final.mp4
```

## 歌词

燕青门 · 古风武侠 · 男女对唱

歌词及英译详见 `docs/lyrics.md`。

## 许可证

MIT
