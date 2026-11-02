# Pika H3 Flex ComfyUI 本地部署指南

[下载完整安装包](https://github.com/Chauntry/Pika-H3-Flex-ComfyUI/releases/latest) · [三套工作流](workflows)

共享三套工作流：T2VA、FL2VA、Ref2VA。含 Qwen rewriter、H3 3D latent upsampler 和 4/6 step 配置，常用参数放在收藏面板。

## 1. 配置

| 项目 | 实测配置 |
|---|---|
| CPU | i5-13600KF，14核20线程 |
| GPU | RTX 3090，24GB显存 |
| 内存 | 64GB |
| 主板 | B760 |
| 硬盘 | 2TB SSD |
| 系统 | Windows 11 25H2，26200.9711 |
| 显卡驱动 | 610.88 |

运行环境：ComfyUI portable，Python 3.13.14，PyTorch 2.14.1+cu130，frontend 1.57.6。实测 ComfyUI 提交：`6d352802d8f8b9133f664a1757d6c6d26390c335`。

## 2. 安装

### 安装 ComfyUI

从 [ComfyUI 官方仓库](https://github.com/Comfy-Org/ComfyUI) 下载 Windows NVIDIA portable 版，解压到例如 `D:\AI\ComfyUI_windows_portable`，运行 `run_nvidia_gpu.bat`。已有安装请更新核心和前端，以支持 H3 节点。

### 安装节点

这三套工作流需要以下节点包：

- 本仓库的 `H3_Sampling_Preset`：4/6步选择、可选首尾帧。
- [MiniMax-H3-Prompt-Rewriter-ComfyUI](https://github.com/pytraveler/MiniMax-H3-Prompt-Rewriter-ComfyUI)：Qwen 提示词改写。
- [Comfyui_Minimax_h3_latent_Upscaler-Plus](https://github.com/xmarre/Comfyui_Minimax_h3_latent_Upscaler-Plus)：3D latent 上采样和细化。

**用脚本安装：** 先安装 Git for Windows，关闭 ComfyUI，在下载包目录打开 PowerShell，执行：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install_nodes.ps1 -PortableRoot 'D:\AI\ComfyUI_windows_portable'
```

该脚本会安装以上三个节点包。已有第三方节点目录会保留，请自行核对版本，避免重复安装。

**手动安装：** 在下载包目录运行以下命令，将路径替换为自己的安装位置：

```powershell
Copy-Item .\custom_nodes\H3_Sampling_Preset 'D:\AI\ComfyUI_windows_portable\ComfyUI\custom_nodes' -Recurse -Force

git clone https://github.com/pytraveler/MiniMax-H3-Prompt-Rewriter-ComfyUI.git 'D:\AI\ComfyUI_windows_portable\ComfyUI\custom_nodes\MiniMax-H3-Prompt-Rewriter-ComfyUI'
git -C 'D:\AI\ComfyUI_windows_portable\ComfyUI\custom_nodes\MiniMax-H3-Prompt-Rewriter-ComfyUI' checkout cedd084f783bcb773648ba5ea3710d267bbc3261

git clone https://github.com/xmarre/Comfyui_Minimax_h3_latent_Upscaler-Plus.git 'D:\AI\ComfyUI_windows_portable\ComfyUI\custom_nodes\Comfyui_Minimax_h3_latent_Upscaler'
git -C 'D:\AI\ComfyUI_windows_portable\ComfyUI\custom_nodes\Comfyui_Minimax_h3_latent_Upscaler' checkout 1ddcc33e9b674aaabbccc3808fe36e1a47bdd36d
```

本工作流的 rewriter 使用 GGUF + llama.cpp。依赖 ComfyUI 自带的 Python 环境，另需按下文配置 llama.cpp。

### 下载模型

`models.json` 包含下载地址、固定版本、文件大小和 SHA256。完整模型约67.26GiB。先查看下载清单：

```powershell
D:\AI\ComfyUI_windows_portable\python_embeded\python.exe .\scripts\download_models.py --comfy-root 'D:\AI\ComfyUI_windows_portable\ComfyUI'
```

下载全套：

```powershell
D:\AI\ComfyUI_windows_portable\python_embeded\python.exe .\scripts\download_models.py --comfy-root 'D:\AI\ComfyUI_windows_portable\ComfyUI' --download
```

脚本支持断点续传并校验 SHA256，已下载且校验通过的文件会跳过。T2VA / FL2VA 可加 `--groups base,rewriter,upscaler`，Ref2VA 另需 `ref2va` 组。

上采样插件还需要以下权重，全套下载命令已包含：

`ComfyUI/models/latent_upscale_models/minimax_h3_latent_upscaler_3d_conv_v1_bf16.safetensors`

文件约0.64GiB，来自 [H3 latent upscaler 模型仓库](https://huggingface.co/LBH-123-AI/Minimax_h3_latent_Upscaler)。即使暂时关闭上采样，也建议下载，以通过工作流的模型选项校验。

模型目录：

```text
ComfyUI/models/
├─ diffusion_models/
│  ├─ minimax_h3_fl2va_pruned_int8_convrot.safetensors
│  └─ minimax_h3_ref2va_pruned_int8_convrot.safetensors
├─ text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors
├─ vae/
│  ├─ minimax_h3_video_vae_int8_convrot.safetensors
│  └─ minimax_h3_audio_vae_fp32.safetensors
├─ loras/
│  ├─ pika_h3_flex_fl2va_v1_bf16.safetensors
│  └─ pika_h3_flex_ref2va_v1_bf16.safetensors
├─ LLM/
│  ├─ Qwen2.5-Omni-7B-Q4_K_M.gguf
│  ├─ mmproj-Qwen2.5-Omni-7B-Q8_0.gguf
│  └─ MiniMax-H3-Prompt-Rewriter-LoRA-Omni-Q8_0.gguf
└─ latent_upscale_models/minimax_h3_latent_upscaler_3d_conv_v1_bf16.safetensors
```

### 配置 llama.cpp

从 [llama.cpp b10310](https://github.com/ggml-org/llama.cpp/releases/tag/b10310) 下载这两个压缩包，解压到同一个目录，例如 `D:\AI\llama-bin`：

- `llama-b10310-bin-win-cuda-13.3-x64.zip`
- `cudart-llama-bin-win-cuda-13.3-x64.zip`

使用启动脚本指定 ComfyUI 和 llama.cpp 所在目录：

```powershell
.\scripts\start_comfyui.cmd "D:\AI\ComfyUI_windows_portable" "D:\AI\llama-bin"
```

也可以在 `ComfyUI/user/minimax_h3_rewriter/llama_bin.txt` 中写入 llama.cpp 可执行文件所在目录。

### 导入工作流

重启 ComfyUI 并刷新浏览器，将 `workflows` 中的 JSON 拖入画布：

- `01_T2V.json`：T2VA。
- `02_Ref2VA.json`：Ref2VA，先上传参考图片。
- `03_FL2VA.json`：FL2VA，按需上传首尾帧。

## 3. 使用

打开右侧收藏（Favorites）面板调整常用参数：

| 参数 | 操作 |
|---|---|
| Prompt | 修改提示词输入框（2010）的 `value` |
| Rewriter | 节点2001的 `bypass=false` 开启，`true` 关闭 |
| 改写结果 | 查看 SaveText（2002），文本保存到 `output/H3/rewrites` |
| 4 / 6 step | H3SamplingPreset 的 `steps` 下拉选择 |
| 时长 | 节点2011设置5、10或15秒 |
| Seed | RandomNoise（129）的 `noise_seed` |
| Upsampler | 节点3006的 `switch=true` 开启，`false` 关闭 |
| 上采样倍率 | 节点3002的 `scale`，默认1.5 |
| 首尾帧 | 两个 H3OptionalImage 的 `image` 下拉中选图片或“空” |

本工作流采用 **4-step 加速**，也保留6-step配置，可直接切换。4-step使用 timestep `1000,750,500,250,0`，video shift=12；节点会输出对应的 sigmas。

上采样使用 **H3 3D latent upscaler + 2步细化**。默认关闭，开启后按设定倍率放大，默认1.5倍。

FL2VA支持：仅首帧、仅尾帧、首尾帧都有、两帧都为空。任务类型自动切换，两帧都为空时按文字生成。

## 4. 常见问题

- **导入后缺节点：** 先安装上述三个节点包，重启 ComfyUI，再刷新浏览器。
- **提示 H3OptionalImage / H3FrameTask / H3SamplingPreset / H3OptionalFrames 是未知包：** 将本仓库 `H3_Sampling_Preset` 文件夹放入 `ComfyUI/custom_nodes`，确认 `__init__.py` 位于该文件夹内。
- **模型下拉找不到文件：** 对照 `models.json` 检查目录、文件名和下载是否完整。
- **Rewriter 找不到 llama.cpp：** 检查传给启动脚本的目录，其中应包含可执行文件和 CUDA DLL。
- **显存不足：** 关闭上采样，减少时长或分辨率。
- **Ref2VA 提示图片不存在：** 在参考图节点上传自己的图片，替换占位文件名。

## 5. 实测耗时

原生分辨率1344×768，24fps，seed=42。每项各跑一次，表内均为已完成的测试。

| 工作流 | 视频时长 | 首轮步数 | 上采样 | 耗时 |
|---|---:|---:|---|---:|
| T2VA | 5秒 | 6 | 关闭 | 4分29.82秒 |
| T2VA | 5秒 | 4 | 关闭 | 3分08.37秒 |
| T2VA | 10秒 | 6 | 关闭 | 16分02.35秒 |
| T2VA | 10秒 | 4 | 关闭 | 14分12.90秒 |
| T2VA | 15秒 | 6 | 关闭 | 31分21.79秒 |
| T2VA | 15秒 | 4 | 关闭 | 21分06.46秒 |
| Ref2VA | 5秒 | 6 | 关闭 | 5分16.03秒 |
| Ref2VA | 10秒 | 6 | 关闭 | 16分06.80秒 |
| Ref2VA | 15秒 | 6 | 关闭 | 31分13.26秒 |
| Ref2VA | 5秒 | 4 | 原生输出阶段 | 约3分29秒 |
| Ref2VA | 5秒 | 4 | 1.5倍＋2步细化 | 10分37.70秒 |
| FL2VA | 5秒 | 6 | 关闭 | 5分41.24秒 |

六步包含当次 rewriter 耗时，四步复用对应的改写文本。Ref2VA四步原生记录的是同一次上采样任务中原生视频保存完成的时间；上采样一行为整次任务总耗时，输出2016×1152。

5/10/15秒按模型帧数要求分别生成124/243/362帧，视频流实际时长约5.167/10.125/15.083秒。
