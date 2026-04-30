---
name: comparessPDF
description: 交互式压缩 PDF，询问压缩率，默认输出到源文件同目录，并自动处理重名输出文件。/ Interactive PDF compressor — prompts for compression level, outputs to source directory by default, and auto-renames on filename collision.
---

# Compress PDF Skill

当用户想压缩单个或多个 PDF 文件，或者直接压缩一个目录里的 PDF 时使用这个 skill。

Use this skill when the user wants to compress one or more PDF files, or all PDFs in a directory.

---

## 行为要求 / Behavior

1. 如果用户没有提供 PDF 路径，先询问输入文件路径。  
   If the user has not provided a PDF path, ask for the input file path first.

2. 让用户在以下模式中确认本次压缩率：  
   Ask the user to choose a compression mode:
   - `high` — 高质量，适合存档 / High quality, good for archiving (300 DPI, JPEG q=85)
   - `balanced` — 均衡压缩，适合大多数场景 / Balanced, suitable for most use cases (200 DPI, JPEG q=80)
   - `extreme` — 极限压缩，适合传输 / Maximum compression, good for sharing (150 DPI, JPEG q=75)
   - `lossless` — 无损优化，仅优化 PDF 结构 / Lossless structural optimization only (qpdf)

3. 如果用户没有明确指定输出路径，默认把新文件放在源文件同目录。  
   If no output path is specified, save the output file in the same directory as the source.

4. 如果目标文件名已存在，不要覆盖旧文件；程序会自动生成 `-2`、`-3` 这样的后缀文件名。  
   Never overwrite an existing file — the tool automatically appends `-2`, `-3`, etc. to avoid collisions.

5. 如果用户给的是目录，默认只处理该目录下的 PDF；需要递归子目录时，使用批量脚本的 `--recursive`。  
   When given a directory, process only top-level PDFs by default; use `--recursive` to include subdirectories.

6. 批量处理目录时，跳过已经由本工具生成的 `*-compressed.pdf`、`*-compressed-2.pdf` 等文件，避免重复压缩。  
   In batch mode, skip previously generated `*-compressed*.pdf` files to prevent double-compression.

7. 完成后明确告诉用户实际输出文件路径和压缩结果。  
   After completion, clearly report the output file path, original size, compressed size, and compression ratio.

---

## 执行方式 / Usage

单文件交互式（不指定模式，弹出菜单）：  
Single file — interactive mode (menu appears when `--mode` is omitted):

```bash
python3 compress_pdf.py INPUT_PDF
```

单文件指定模式：  
Single file — specify mode directly:

```bash
python3 compress_pdf.py INPUT_PDF --mode MODE
```

批量处理多个文件或目录：  
Batch — multiple files or directories:

```bash
python3 compress_pdf_batch.py FILE_OR_DIR [MORE_FILES_OR_DIRS] --mode MODE
```

批量递归子目录：  
Batch — recursive subdirectories:

```bash
python3 compress_pdf_batch.py INPUT_DIR --mode MODE --recursive
```

---

## 依赖检查 / Dependencies

| 依赖 / Dependency | macOS | Linux | Windows | 用途 / Required for |
|---|---|---|---|---|
| Python `click` | `pip install -r requirements.txt` | 同左 / same | 同左 / same | CLI 框架 / CLI framework |
| Ghostscript | `brew install ghostscript` | `sudo apt install ghostscript` | [ghostscript.com](https://ghostscript.com/releases/) | `high`, `balanced`, `extreme` 模式 |
| qpdf | `brew install qpdf` | `sudo apt install qpdf` | [qpdf.sourceforge.net](https://qpdf.sourceforge.net/) | `lossless` 模式 |

> **Windows 注意 / Windows note**: Ghostscript 在 Windows 下命令为 `gswin64c`，脚本内已自动识别无需手动指定。  
> The script auto-detects `gswin64c` / `gswin32c` on Windows — no manual configuration needed.

---

## 结果说明 / Output Rules

- 默认输出文件名：`原文件名-compressed.pdf`  
  Default output name: `{original-name}-compressed.pdf`
- 已存在同名文件时自动变为：`原文件名-compressed-2.pdf`，依次递增  
  On collision, automatically becomes `-compressed-2.pdf`, `-compressed-3.pdf`, etc.
- 批量模式会自动跳过已生成的压缩结果文件  
  Batch mode skips already-generated compressed files automatically