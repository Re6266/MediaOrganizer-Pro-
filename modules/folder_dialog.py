"""Windows system pickers for a locally launched desktop session."""
import base64
import json
import subprocess
import sys
from pathlib import Path


def choose_paths(mode):
    if sys.platform != "win32":
        raise RuntimeError("当前桌面选择器仅支持 Windows。")
    if mode not in ("files", "folder"):
        raise ValueError("不支持的选择方式")
    # JSON is written as UTF-8 bytes so Chinese paths survive Windows code pages.
    setup = """$ErrorActionPreference = 'Stop'
Add-Type -TypeDefinition 'using System; using System.Runtime.InteropServices; public static class ScreenDpi { [DllImport("user32.dll")] public static extern bool SetProcessDpiAwarenessContext(IntPtr value); [DllImport("user32.dll")] public static extern bool SetProcessDPIAware(); }'
try {
    if (-not [ScreenDpi]::SetProcessDpiAwarenessContext([IntPtr](-4))) { [ScreenDpi]::SetProcessDPIAware() | Out-Null }
} catch { [ScreenDpi]::SetProcessDPIAware() | Out-Null }
Add-Type -AssemblyName System.Windows.Forms
[System.Windows.Forms.Application]::EnableVisualStyles()
$owner = New-Object System.Windows.Forms.Form
$owner.TopMost = $true
$owner.ShowInTaskbar = $false
$owner.StartPosition = 'Manual'
$owner.Location = New-Object System.Drawing.Point(-32000,-32000)
$owner.Show()
"""
    if mode == "files":
        picker = """$dialog = New-Object System.Windows.Forms.OpenFileDialog
$dialog.Title = '选择文件'
$dialog.Filter = '所有文件 (*.*)|*.*'
$dialog.Multiselect = $true
$selected = @()
if ($dialog.ShowDialog($owner) -eq [System.Windows.Forms.DialogResult]::OK) { $selected = @($dialog.FileNames) }
"""
    else:
        source = str(Path(__file__).with_name("windows_folder_picker.cs")).replace("'", "''")
        picker = f"""Add-Type -Path '{source}'
$selected = @()
$chosen = [WindowsFolderPicker]::Choose($owner.Handle)
if ($chosen) {{ $selected = @($chosen) }}
"""
    finish = """$json = ConvertTo-Json -InputObject @($selected) -Compress
$bytes = [System.Text.Encoding]::UTF8.GetBytes($json)
$out = [Console]::OpenStandardOutput()
$out.Write($bytes, 0, $bytes.Length)
if ($dialog) { $dialog.Dispose() }
$owner.Dispose()
"""
    encoded = base64.b64encode((setup + picker + finish).encode("utf-16-le")).decode("ascii")
    try:
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-STA", "-EncodedCommand", encoded],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
            creationflags=subprocess.CREATE_NO_WINDOW, timeout=300,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("选择窗口未响应，请关闭窗口后重试。") from exc
    if result.returncode:
        raise RuntimeError("无法打开系统选择窗口，请通过桌面启动程序后重试。")
    try:
        selected = json.loads(result.stdout.decode("utf-8"))
        if not isinstance(selected, list) or not all(isinstance(path, str) for path in selected):
            raise ValueError("invalid picker result")
        return selected
    except (UnicodeError, ValueError) as exc:
        raise RuntimeError("无法读取系统选择结果。") from exc


def choose_folder():
    paths = choose_paths("folder")
    return paths[0] if paths else ""
