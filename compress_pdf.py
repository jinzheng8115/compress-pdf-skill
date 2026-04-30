#!/usr/bin/env python3
"""
compress_pdf.py — PDF 压缩工具（基于 Ghostscript / qpdf）

支持四种压缩模式:
  high     — 300 DPI, JPEG q=85（默认，接近第三方工具效果）
  balanced — 200 DPI, JPEG q=80（文件更小，质量可接受）
  extreme  — 150 DPI, JPEG q=75（最大压缩率）
  lossless — 仅优化 PDF 结构，不降采样（使用 qpdf）
"""

import platform
import subprocess
import shutil
import sys
from pathlib import Path

import click

# ── 平台相关 / Platform ───────────────────────────────────
# Windows uses gswin64c/gswin32c; macOS and Linux use gs
_GS_CMD: str = (
    next(
        (name for name in ("gswin64c", "gswin32c") if shutil.which(name)),
        "gswin64c",
    )
    if platform.system() == "Windows"
    else "gs"
)


def _gs_install_hint() -> str:
    """Return platform-appropriate Ghostscript install hint."""
    os_name = platform.system()
    if os_name == "Darwin":
        return "brew install ghostscript"
    if os_name == "Windows":
        return "https://ghostscript.com/releases/ (将 bin/ 目录加入 PATH)"
    return "sudo apt install ghostscript  # Ubuntu/Debian"


def _qpdf_install_hint() -> str:
    """Return platform-appropriate qpdf install hint."""
    os_name = platform.system()
    if os_name == "Darwin":
        return "brew install qpdf"
    if os_name == "Windows":
        return "https://qpdf.sourceforge.net/ (将 bin/ 目录加入 PATH)"
    return "sudo apt install qpdf  # Ubuntu/Debian"

# ── 各模式参数配置 ─────────────────────────────────────────
MODES: dict[str, dict] = {
    "high": {
        "dpi": 300,
        "jpeg_q": 85,
        "desc": "高质量 (300 DPI, JPEG q=85)，接近第三方工具效果",
    },
    "balanced": {
        "dpi": 200,
        "jpeg_q": 80,
        "desc": "均衡 (200 DPI, JPEG q=80)，文件更小",
    },
    "extreme": {
        "dpi": 150,
        "jpeg_q": 75,
        "desc": "极限压缩 (150 DPI, JPEG q=75)，最大压缩率",
    },
    "lossless": {
        "desc": "无损优化，仅优化 PDF 结构（使用 qpdf）",
    },
}

MODE_ALIASES: dict[str, str] = {
    str(index): name
    for index, name in enumerate(MODES.keys(), start=1)
}


def check_tool(name: str, install_hint: str) -> None:
    """检查外部工具是否可用，不可用则退出。/ Check that an external tool is available."""
    if shutil.which(name) is None:
        click.secho(
            f"错误: 未找到 {name}，请先安装: {install_hint}",
            fg="red",
            err=True,
        )
        sys.exit(1)


def file_size_mb(path: Path) -> float:
    return path.stat().st_size / 1_048_576


def prompt_for_mode() -> str:
    """交互式选择压缩模式。"""
    click.echo("\n请选择压缩模式:\n")
    for index, (name, cfg) in enumerate(MODES.items(), start=1):
        click.secho(f"  {index}. {name:<10}", fg="cyan", nl=False)
        click.echo(cfg["desc"])

    while True:
        choice = click.prompt("请输入模式编号或名称", default="1", show_default=True).strip().lower()
        if choice in MODE_ALIASES:
            return MODE_ALIASES[choice]
        if choice in MODES:
            return choice
        click.secho("无效模式，请输入编号 1-4 或模式名称。", fg="red", err=True)


def default_output_path(input_path: Path) -> Path:
    """生成默认输出路径，默认与源文件同目录。"""
    return input_path.with_name(f"{input_path.stem}-compressed.pdf")


def next_available_path(output_path: Path) -> Path:
    """如果目标文件已存在，则自动追加递增后缀。"""
    if not output_path.exists():
        return output_path

    index = 2
    while True:
        candidate = output_path.with_name(f"{output_path.stem}-{index}{output_path.suffix}")
        if not candidate.exists():
            return candidate
        index += 1


def resolve_output_path(input_path: Path, output_path: Path | None) -> tuple[Path, bool]:
    """解析最终输出路径，并在发生重名时自动避让。"""
    requested_output = output_path or default_output_path(input_path)
    if input_path.resolve(strict=False) == requested_output.resolve(strict=False):
        click.secho("错误: 输入和输出文件不能相同", fg="red", err=True)
        sys.exit(1)

    final_output = next_available_path(requested_output)
    return final_output, final_output != requested_output


def resolve_mode(mode: str | None) -> str:
    """解析压缩模式；未指定时进入交互式选择。"""
    if mode is None:
        return prompt_for_mode()
    return mode.lower()


def compress_with_gs(input_path: Path, output_path: Path, dpi: int, jpeg_q: int) -> None:
    """调用 Ghostscript 压缩 PDF。"""
    cmd = [
        _GS_CMD,
        "-sDEVICE=pdfwrite",
        "-dCompatibilityLevel=1.5",
        "-dNOPAUSE",
        "-dQUIET",
        "-dBATCH",
        "-dDetectDuplicateImages=true",
        "-dCompressFonts=true",
        "-dSubsetFonts=true",
        "-dAutoFilterColorImages=false",
        "-dAutoFilterGrayImages=false",
        "-dColorImageFilter=/DCTEncode",
        "-dGrayImageFilter=/DCTEncode",
        f"-dJPEGQ={jpeg_q}",
        "-dDownsampleColorImages=true",
        "-dDownsampleGrayImages=true",
        "-dDownsampleMonoImages=false",
        "-dColorImageDownsampleType=/Bicubic",
        "-dGrayImageDownsampleType=/Bicubic",
        f"-dColorImageResolution={dpi}",
        f"-dGrayImageResolution={dpi}",
        f"-sOutputFile={output_path}",
        str(input_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        click.secho(f"Ghostscript 错误:\n{result.stderr}", fg="red", err=True)
        sys.exit(result.returncode)


def compress_with_qpdf(input_path: Path, output_path: Path) -> None:
    """调用 qpdf 进行无损结构优化。"""
    cmd = [
        "qpdf",
        "--linearize",
        "--compress-streams=y",
        "--object-streams=generate",
        "--recompress-flate",
        "--compression-level=9",
        str(input_path),
        str(output_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode not in (0, 3):  # qpdf 返回 3 表示警告但成功
        click.secho(f"qpdf 错误:\n{result.stderr}", fg="red", err=True)
        sys.exit(result.returncode)


# ── CLI 入口 ──────────────────────────────────────────────
@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("input_pdf", type=click.Path(dir_okay=False, path_type=Path), required=False)
@click.argument("output_pdf", type=click.Path(dir_okay=False, path_type=Path), required=False)
@click.option(
    "-m",
    "--mode",
    type=click.Choice(list(MODES.keys()), case_sensitive=False),
    default=None,
    help="压缩模式；不传时进入交互式选择",
)
@click.option("--list-modes", is_flag=True, help="列出所有压缩模式说明")
def main(
    input_pdf: Path,
    output_pdf: Path | None,
    mode: str | None,
    list_modes: bool,
) -> None:
    """PDF 压缩工具 — 基于 Ghostscript / qpdf

    \b
    INPUT_PDF   输入文件
    OUTPUT_PDF  输出文件（可选，默认在原文件同目录生成 *-compressed.pdf）

    \b
    模式说明:
      high     — 300 DPI, JPEG q=85（默认）
      balanced — 200 DPI, JPEG q=80
      extreme  — 150 DPI, JPEG q=75
      lossless — 无损结构优化（qpdf）
    """
    if list_modes:
        click.echo("\n可用压缩模式:\n")
        for name, cfg in MODES.items():
            click.secho(f"  {name:<10}", fg="cyan", nl=False)
            click.echo(cfg["desc"])
        click.echo()
        return

    # 必须提供输入文件
    if input_pdf is None:
        click.secho("错误: 请指定输入文件，或使用 --list-modes 查看模式说明", fg="red", err=True)
        sys.exit(1)

    if not input_pdf.exists():
        click.secho(f"错误: 文件不存在: {input_pdf}", fg="red", err=True)
        sys.exit(1)

    mode = resolve_mode(mode)
    output_pdf, output_renamed = resolve_output_path(input_pdf, output_pdf)

    # 检查依赖
    if mode == "lossless":
        check_tool("qpdf", _qpdf_install_hint())
    else:
        check_tool(_GS_CMD, _gs_install_hint())

    # 打印摘要
    click.secho("=== PDF 压缩工具 ===", fg="cyan")
    click.echo(f"输入: {input_pdf}")
    click.echo(f"输出: {output_pdf}")
    click.echo(f"模式: ", nl=False)
    click.secho(f"{mode}", fg="yellow", nl=False)
    click.echo(f"  — {MODES[mode]['desc']}")
    if output_renamed:
        click.secho(f"检测到同名输出，已自动改名为: {output_pdf.name}", fg="yellow")
    click.echo()

    input_size = file_size_mb(input_pdf)
    click.echo(f"原始大小: {input_size:.2f} MB")
    click.echo()

    # 执行压缩
    if mode == "lossless":
        click.echo("使用 qpdf 进行无损结构优化...")
        compress_with_qpdf(input_pdf, output_pdf)
    else:
        cfg = MODES[mode]
        click.echo(f"使用 Ghostscript 压缩 ({cfg['dpi']} DPI, JPEG q={cfg['jpeg_q']})...")
        compress_with_gs(input_pdf, output_pdf, cfg["dpi"], cfg["jpeg_q"])

    # 结果报告
    if output_pdf.exists():
        output_size = file_size_mb(output_pdf)
        ratio = (1 - output_size / input_size) * 100
        click.echo()
        click.secho("✓ 压缩完成", fg="green")
        click.echo(f"原始大小: {input_size:.2f} MB")
        click.echo(f"压缩后:   {output_size:.2f} MB")
        click.echo(f"压缩率:   {ratio:.1f}%")
        click.echo(f"输出文件: {output_pdf}")
    else:
        click.secho("✗ 压缩失败，未生成输出文件", fg="red", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
