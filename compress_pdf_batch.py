#!/usr/bin/env python3
"""
compress_pdf_batch.py — 批量 PDF 压缩工具（基于 Ghostscript / qpdf）
"""

import re
import sys
from pathlib import Path

import click

import compress_pdf

COMPRESSED_OUTPUT_PATTERN = re.compile(r"-compressed(?:-\d+)?$", re.IGNORECASE)


def is_generated_output(path: Path) -> bool:
    """判断文件是否为本工具生成的压缩结果。"""
    return bool(COMPRESSED_OUTPUT_PATTERN.search(path.stem))


def collect_input_pdfs(input_paths: tuple[Path, ...], recursive: bool) -> list[Path]:
    """收集待压缩 PDF，目录输入默认跳过已生成的压缩文件。"""
    discovered: dict[str, Path] = {}
    for input_path in input_paths:
        if input_path.is_dir():
            pattern = "**/*.pdf" if recursive else "*.pdf"
            candidates = sorted(candidate for candidate in input_path.glob(pattern) if candidate.is_file())
        else:
            candidates = [input_path]

        for candidate in candidates:
            if candidate.suffix.lower() != ".pdf":
                continue
            if is_generated_output(candidate):
                continue
            discovered[str(candidate.resolve(strict=False))] = candidate
    return sorted(discovered.values(), key=lambda path: (len(path.parts), str(path)))


def compress_one_file(input_pdf: Path, mode: str) -> tuple[Path, bool, float, float]:
    """压缩单个 PDF，返回输出文件与统计信息。"""
    output_pdf, output_renamed = compress_pdf.resolve_output_path(input_pdf, None)
    input_size = compress_pdf.file_size_mb(input_pdf)

    if mode == "lossless":
        compress_pdf.compress_with_qpdf(input_pdf, output_pdf)
    else:
        cfg = compress_pdf.MODES[mode]
        compress_pdf.compress_with_gs(input_pdf, output_pdf, cfg["dpi"], cfg["jpeg_q"])

    output_size = compress_pdf.file_size_mb(output_pdf)
    return output_pdf, output_renamed, input_size, output_size


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument(
    "input_paths",
    nargs=-1,
    type=click.Path(exists=True, path_type=Path),
)
@click.option(
    "-m",
    "--mode",
    type=click.Choice(list(compress_pdf.MODES.keys()), case_sensitive=False),
    default=None,
    help="压缩模式；不传时进入交互式选择",
)
@click.option("-r", "--recursive", is_flag=True, help="目录输入时递归处理子目录")
def main(input_paths: tuple[Path, ...], mode: str | None, recursive: bool) -> None:
    """批量压缩多个 PDF 文件或整个目录中的 PDF。"""
    if not input_paths:
        click.secho("错误: 请至少提供一个 PDF 文件或目录", fg="red", err=True)
        sys.exit(1)

    mode = compress_pdf.resolve_mode(mode)
    if mode == "lossless":
        compress_pdf.check_tool("qpdf", compress_pdf._qpdf_install_hint())
    else:
        compress_pdf.check_tool(compress_pdf._GS_CMD, compress_pdf._gs_install_hint())

    pdf_files = collect_input_pdfs(input_paths, recursive)
    if not pdf_files:
        click.secho("错误: 未找到可压缩的 PDF 文件", fg="red", err=True)
        sys.exit(1)

    click.secho("=== PDF 批量压缩工具 ===", fg="cyan")
    click.echo(f"模式: {mode}  — {compress_pdf.MODES[mode]['desc']}")
    click.echo(f"文件数: {len(pdf_files)}")

    success_count = 0
    failures: list[tuple[Path, int]] = []
    for index, input_pdf in enumerate(pdf_files, start=1):
        click.echo()
        click.secho(f"[{index}/{len(pdf_files)}] {input_pdf}", fg="cyan")
        try:
            output_pdf, output_renamed, input_size, output_size = compress_one_file(input_pdf, mode)
            ratio = (1 - output_size / input_size) * 100
            if output_renamed:
                click.secho(f"检测到同名输出，已自动改名为: {output_pdf.name}", fg="yellow")
            click.secho(f"✓ 输出文件: {output_pdf}", fg="green")
            click.echo(f"  原始大小: {input_size:.2f} MB")
            click.echo(f"  压缩后:   {output_size:.2f} MB")
            click.echo(f"  压缩率:   {ratio:.1f}%")
            success_count += 1
        except SystemExit as exc:
            exit_code = exc.code if isinstance(exc.code, int) else 1
            failures.append((input_pdf, exit_code))
            click.secho(f"✗ 压缩失败: {input_pdf}", fg="red", err=True)

    click.echo()
    if failures:
        click.secho(
            f"批量压缩完成: 成功 {success_count} 个，失败 {len(failures)} 个",
            fg="yellow",
        )
        for failed_path, exit_code in failures:
            click.echo(f"  - {failed_path} (exit={exit_code})")
        sys.exit(1)

    click.secho(f"批量压缩完成: 共成功处理 {success_count} 个 PDF", fg="green")


if __name__ == "__main__":
    main()