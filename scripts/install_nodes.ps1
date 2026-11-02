param([Parameter(Mandatory=$true)][string]$PortableRoot, [switch]$InstallTransformersExtras)
$ErrorActionPreference = 'Stop'
$portable = (Resolve-Path -LiteralPath $PortableRoot).Path
$comfy = Join-Path $portable 'ComfyUI'
$python = Join-Path $portable 'python_embeded/python.exe'
if (!(Test-Path -LiteralPath (Join-Path $comfy 'main.py')) -or !(Test-Path -LiteralPath $python)) { throw 'Expected Windows portable root containing ComfyUI and python_embeded.' }
$package = Split-Path -Parent $PSScriptRoot
$nodes = Join-Path $comfy 'custom_nodes'
New-Item -ItemType Directory -Force -Path $nodes | Out-Null
Copy-Item -LiteralPath (Join-Path $package 'custom_nodes/H3_Sampling_Preset') -Destination $nodes -Recurse -Force
$plugins = @(
 @{Name='MiniMax-H3-Prompt-Rewriter-ComfyUI'; Url='https://github.com/pytraveler/MiniMax-H3-Prompt-Rewriter-ComfyUI.git'; Commit='cedd084f783bcb773648ba5ea3710d267bbc3261'},
 @{Name='Comfyui_Minimax_h3_latent_Upscaler'; Url='https://github.com/xmarre/Comfyui_Minimax_h3_latent_Upscaler-Plus.git'; Commit='1ddcc33e9b674aaabbccc3808fe36e1a47bdd36d'}
)
foreach ($plugin in $plugins) {
 $target = Join-Path $nodes $plugin.Name
 if (Test-Path -LiteralPath $target) { Write-Host "Already exists; leaving existing plugin unchanged: $target"; continue }
 & git clone $plugin.Url $target
 if ($LASTEXITCODE -ne 0) { throw 'git clone failed' }
 & git -C $target checkout --detach $plugin.Commit
 if ($LASTEXITCODE -ne 0) { throw 'git checkout failed' }
}
if ($InstallTransformersExtras) {
 & $python -s -m pip install -r (Join-Path $nodes 'MiniMax-H3-Prompt-Rewriter-ComfyUI/requirements.txt')
 if ($LASTEXITCODE -ne 0) { throw 'requirements installation failed' }
}
Write-Host 'Nodes installed. GGUF defaults do not require PEFT/bitsandbytes/accelerate. Download models and set llama.cpp runtime as documented, then restart ComfyUI.'

