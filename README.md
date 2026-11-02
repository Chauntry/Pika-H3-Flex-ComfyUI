# Pika H3 Flex ComfyUI 本地部署指南

[下载完整安装包](https://github.com/Chauntry/Pika-H3-Flex-ComfyUI/releases/latest) · [三套工作流](workflows) · [完整实测表](docs/完整实测表.md)

共享三套 Pika H3 Flex ComfyUI 工作流：T2VA、FL2VA、Ref2VA。基于官方模板，加入 Qwen rewriter、H3 3D latent upsampler、4/6步选择和可选首尾帧。常用参数放在收藏面板。

仓库包含工作流 JSON、辅助节点、节点安装脚本、模型下载脚本和实测记录。JSON 不包含模型与运行环境，安装步骤见下文。

实测硬件配置：

| 配件 | 配置 |
|---|---|
| CPU | Intel Core i5-13600KF，14核20线程 |
| 显卡 | NVIDIA GeForce RTX 3090，24GB显存 |
| 内存 | 64GB，系统可用总量约63.8GiB |
| 主板 | ASUS ROG STRIX B760-G GAMING WIFI |
| 硬盘 | ZHITAI（致态）TiPlus7100 2TB |
| BIOS | 1220 |
| 系统 | Windows 11 25H2，Build 26200.9711 |
| NVIDIA 驱动 | 610.88 |

内存条品牌、具体型号与频率，以及电源、散热和机箱型号尚未确认。这里列出的是已从本机读取或核实的配置。

完整耗时见 [实测表](docs/完整实测表.md)。

## 1. 要装什么

| 组件 | 用途 | 是否需要 |
|---|---|---|
| NVIDIA 驱动 + Windows NVIDIA 版 ComfyUI portable | 基础运行环境，便携包自带 Python / PyTorch | 必须 |
| Git for Windows | 安装并固定第三方节点版本 | 使用安装脚本时需要 |
| 本仓库 `custom_nodes/H3_Sampling_Preset` | 4/6 步、首尾帧选“空”、自动判断任务 | 三套 JSON 都需要 |
| MiniMax-H3-Prompt-Rewriter-ComfyUI | Qwen 提示词改写 | JSON 内保留节点，建议安装；开关可关闭计算 |
| Comfyui_Minimax_h3_latent_Upscaler-Plus | 3D latent 上采样和细化 | JSON 内保留节点，建议安装；默认不开计算 |
| H3 主模型、文本编码器、两种 VAE、Flex LoRA | 视频和声音生成 | 必须，见模型清单 |
| Qwen Omni GGUF + projector + rewriter LoRA + llama.cpp CUDA runtime | 本地改写 | 开 rewriter 时需要 |
| H3 3D upscaler 权重 | latent 上采样 | 本仓库完整 JSON 建议安装，避免模型下拉校验失败 |

关闭节点计算不代表能删除其安装：ComfyUI 导入时仍需认识工作流中的节点类型。本仓库辅助节点没有注册到 Manager，出现“未知包 H3OptionalImage / H3FrameTask / H3SamplingPreset / H3OptionalFrames”时，复制本仓库节点目录并重启即可，不必搜索同名 pip 包。

实测机器：RTX 3090 24GB、64GB 内存、i5-13600KF，Windows 原生 portable。已跑通不等于适用于所有显存配置；下载与解压另留空间，完整权重大小可运行下方预览命令查看。这里不要求 WSL。

## 2. 安装顺序

### A. 先让 ComfyUI 本体启动

从 [ComfyUI 官方仓库](https://github.com/Comfy-Org/ComfyUI) 的 Windows portable 安装入口下载 NVIDIA 版本，解压到路径较短的目录，例如 `D:\AI\ComfyUI_windows_portable`，运行 `run_nvidia_gpu.bat`。

本地实际验证的是 ComfyUI `6d352802d8f8b9133f664a1757d6c6d26390c335`、frontend `1.57.6`、Python `3.13.14`、Torch `2.14.1+cu130`。旧版不一定包含 H3 和 ComfySwitchNode / ComfyMathExpression，先升级官方核心和前端。版本号仅为复现记录，不代表其他版本不能用。

### B. 安装三个节点目录

关闭 ComfyUI，在本仓库目录打开 PowerShell（先安装 Git for Windows）：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install_nodes.ps1 -PortableRoot 'D:\AI\ComfyUI_windows_portable'
```

脚本复制本仓库辅助节点，克隆两个第三方插件到固定提交，本包使用 GGUF + llama.cpp 路线，默认不安装 PEFT、accelerate、bitsandbytes，也不要求 llama-cpp-python；本机实测同样没有这三个额外包。只有你自行改为 Transformers 路线时，才加 `-InstallTransformersExtras`，脚本会使用 **portable 自带 Python** 安装上游 requirements。不会安装 ComfyUI 本体、不会下载几十 GB 权重、不会改写已有第三方插件目录。若已有插件，请对照版本手动更新；不要同时放两份同一插件。

手动安装也可以：把 `custom_nodes/H3_Sampling_Preset` 整个文件夹复制到 `ComfyUI/custom_nodes/`，再依两个第三方项目说明安装。最终应为 `custom_nodes/H3_Sampling_Preset/__init__.py`，不要多嵌套一层仓库目录。

第三方固定版本：

- [Rewriter](https://github.com/pytraveler/MiniMax-H3-Prompt-Rewriter-ComfyUI)：`cedd084f783bcb773648ba5ea3710d267bbc3261`
- [H3 3D Upscaler Plus](https://github.com/xmarre/Comfyui_Minimax_h3_latent_Upscaler-Plus)：`1ddcc33e9b674aaabbccc3808fe36e1a47bdd36d`

### C. 下载模型到正确目录

本仓库 `models.json` 列出每个文件的固定来源版本、字节数、SHA256 和相对路径。路径相对于 `ComfyUI/models/`。**不需要把两套主模型都加载进显存，但 Ref2VA 使用自己的权重。**

先只预览，不下载：

```powershell
D:\AI\ComfyUI_windows_portable\python_embeded\python.exe .\scripts\download_models.py --comfy-root 'D:\AI\ComfyUI_windows_portable\ComfyUI'
```

确认空间后下载全套：

```powershell
D:\AI\ComfyUI_windows_portable\python_embeded\python.exe .\scripts\download_models.py --comfy-root 'D:\AI\ComfyUI_windows_portable\ComfyUI' --download
```

只下载 T2V / FL2VA 基础模型和 rewriter：加 `--groups base,rewriter,upscaler`。Ref2VA 再加 `ref2va`。完整 JSON 即使关闭上采样，提交校验仍可能检查其模型下拉，因此建议也下载仅约 0.64 GiB 的 upscaler 权重；关闭开关节省的是运行计算。下载脚本使用 Python 标准库，无额外依赖；已有文件校验通过会跳过。网络中断可重跑，支持服务器接受 Range 时从 `.part` 续传；服务器忽略 Range 时会重新下载。大小或 SHA256 不符会停止，不会把未校验文件当成模型；也可用 Hugging Face 官方工具下载后按清单摆放。需要 Python 3.11+。

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

Qwen3-VL 32B 是 H3 的文本编码器；Qwen2.5-Omni 7B 是单独的 prompt rewriter，二者不是同一个模型。

### D. 给 GGUF rewriter 配 llama.cpp

从 [llama.cpp b10310](https://github.com/ggml-org/llama.cpp/releases/tag/b10310) 下载 `llama-b10310-bin-win-cuda-13.3-x64.zip` 和 `cudart-llama-bin-win-cuda-13.3-x64.zip`，解压到同一目录，例如 `D:\AI\llama-bin`。下载地址、大小、SHA256 见 `docs/llama-runtime-downloads.json`。这是本机已验证的组合；需支持该 CUDA runtime 的 NVIDIA 驱动。

在 `ComfyUI/user/minimax_h3_rewriter/llama_bin.txt` 中写入实际可执行文件所在目录，例如只有一行：

```text
D:\AI\llama-bin
```

也可在启动 ComfyUI 前设置环境变量 `MINIMAX_H3_LLAMA_BIN` 指向这个目录。文件夹内应有 llama.cpp 可执行文件和 CUDA DLL，而非只放 ZIP。

可以用本仓库启动器传入这两个目录（先关闭旧的 ComfyUI 服务）：

```powershell
.\scripts\start_comfyui.cmd "D:\AI\ComfyUI_windows_portable" "D:\AI\llama-bin"
```

### E. 重启并导入

重启 ComfyUI 后刷新浏览器，再将 `workflows/01_T2V.json`、`02_Ref2VA.json` 或 `03_FL2VA.json` 拖到画布。不是把仓库 ZIP 拖进去。

公开包不带测试使用的人像图片。Ref2VA 需要先在参考图节点上传你自己的图片；占位文件名 `UPLOAD_REFERENCE_IMAGE.png` 不是漏下载的模型。FL2VA 默认两帧都为空，请按需上传。

## 3. 怎么改参数

打开右侧收藏（Favorites）面板，三份工作流都保留常用参数。前端不同语言的字段名可能略有不同，以节点和 widget 名为准。

| 想改什么 | 操作 |
|---|---|
| 原始 prompt | 修改 `PrimitiveStringMultiline`（编号 2010）的 `value`，这里输入你自己的中文描述 |
| 关闭 rewriter | `MiniMaxH3PromptWriterOmni`（2001）的 `bypass=true`；false 为开启。关闭时原始 prompt 直通，不需要手动改连线 |
| 改写后文本 | 查看 `SaveText`（2002）输出；保存到 ComfyUI output 下的 `H3/rewrites`。不要把已经改写的长文误认成唯一输入框 |
| 4 / 6 步 | `H3SamplingPreset` 的 `steps` 下拉选择 4 或 6，推荐先用 6 |
| 5 / 10 / 15 秒 | 时长输入节点（2011），同时传给 rewriter 与帧数表达式 |
| seed | `RandomNoise`（129）的 `noise_seed`；对比时固定 |
| 打开上采样 | `ComfySwitchNode`（3006）的 `switch=true`，false 为原生视频；默认 false |
| 放大倍率 | `MinimaxH3LatentUpscaler3DRefineHandoff`（3002）的 `scale`；默认 1.5 |
| FL2VA 首 / 尾帧 | 两个 `H3OptionalImage` 的 `image` 下拉中选图片或“空”，不用单独切开关 |

FL2VA：只有首帧→I2AV，只有尾帧→L2AV，两帧都有→FL2AV，两帧都为空→T2AV；任务会同步给 rewriter。**空是没有图片输入，不是黑色图或空 latent。** Ref2VA 的参考图用于身份/内容参考，不等同首帧约束。

4 步是用户自定义实验：原始 timestep `1000,750,500,250,0`，经 video shift=12 变换，输出 sigmas `1,36/37,12/13,0.8,0`。6 步使用官方模板的预设。7 个边界数字对应 6 次更新，5 个对应 4 次更新。不要再额外对这些 sigma 加一次 shift；audio 的映射由 H3 原生节点处理。

上采样使用社区 **3D latent upscaler + 2 步细化**，不是 Real-ESRGAN，也不是官方 Flex 首轮采样。首轮 4/6 步不控制这 2 步细化。它能增加尺寸，不能保证恢复真实人脸细节；开启会增加显存和耗时。关闭开关会跳过该分支的计算。

## 4. 常见问题

- **JSON 拖进去提示缺节点：** 先装上面三个节点目录，重启服务再刷新网页。仅刷新无法加载新的 Python 节点。
- **看不到“空”：** 确认使用 `H3OptionalImage`，且本仓库节点文件为新版；旧浏览器页需刷新。内置 LoadImage 不提供这个选项。
- **模型下拉没有文件：** 按 `models.json` 检查目录、文件名和下载完整性，重启/刷新。外置模型目录需自行配置 `extra_model_paths.yaml`。
- **Rewriter 找不到 runtime：** 检查 `llama_bin.txt`、可执行文件和 DLL，不要只安装 Python 的 llama 包代替这里配置的二进制。
- **CUDA OOM：** 先关上采样、减少时长或分辨率；不要同时开多个视频任务。本包不保证低于 24GB 显存能跑同样设置。
- **首次耗时特别长：** 下载、模型装载和首次初始化会影响耗时，表格须写清测量口径。
- **为什么 5 秒是 124 帧：** 工作流按 H3 的帧数约束补齐：`a*24 + (5-a*24)%17`。5/10/15 秒分别 124/243/362 帧；容器实际时长可能略有不同。

## 5. 实测与来源

测试数据见 `docs/`；四步 5/10/15 秒均已实际运行成功，每种时长各测一次。测试所用原始/改写提示词在 `docs/benchmark-prompts/`，公开 JSON 的默认中性示例与测试文本不同；复现实测请替换为对应文件，并关闭 rewriter 复用改写结果。安装脚本是交付工具，未在另一台全新机器做完整安装验收；本机的三个工作流、rewriter、可选帧节点与上采样已分别验证。

- [官方 ComfyUI 教程](https://docs.comfy.org/tutorials/video/pika/pika-h3-flex)
- [Pika-H3-Flex 官方代码](https://github.com/Pika-Labs/Pika-H3-Flex)
- [官方工作流模板](https://github.com/Comfy-Org/workflow_templates)
- [Comfy-Org 模型](https://huggingface.co/Comfy-Org/MiniMax-H3)
- [LightX2V rewriter 原始适配器](https://huggingface.co/lightx2v/MiniMax-H3-Prompt-Rewriter-LoRA-Omni)
- [GGUF rewriter 插件](https://github.com/pytraveler/MiniMax-H3-Prompt-Rewriter-ComfyUI)
- [3D latent upscaler 插件](https://github.com/xmarre/Comfyui_Minimax_h3_latent_Upscaler-Plus)
- [3D latent upscaler 权重](https://huggingface.co/LBH-123-AI/Minimax_h3_latent_Upscaler)

本仓库不分发模型、第三方插件源代码、私人图片或生成视频。辅助节点与脚本使用本仓库 LICENSE；官方模板衍生工作流及模型、插件各自遵守上游许可，不能将本仓库许可视为上游模型的商业使用授权。





