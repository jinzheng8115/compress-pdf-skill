# PDF 压缩工具 / PDF Compressor

基于 Ghostscript / qpdf 的交互式 PDF 压缩工具，支持四种压缩模式，自动重命名避免覆盖已有文件。

An interactive PDF compression tool powered by Ghostscript / qpdf. Supports four compression modes and auto-renames output files to avoid overwriting existing results.

---

## 系统依赖 / System Requirements

| 依赖 | macOS | Linux | Windows |
| --- | --- | --- | --- |
| Ghostscript | `brew install ghostscript` | `sudo apt install ghostscript` | [ghostscript.com/releases](https://ghostscript.com/releases/) |
| qpdf | `brew install qpdf` | `sudo apt install qpdf` | [qpdf.sourceforge.net](https://qpdf.sourceforge.net/) |

> **Windows**: Ghostscript 在 Windows 下命令名为 `gswin64c`，脚本已自动识别，无需额外配置。  
> Python 命令在 Windows 下通常为 `python`，其他平台为 `python3`。

---

## 安装 Python 依赖 / Install Python Dependencies

```bash
pip install -r requirements.txt
```

---

## 快速上手 / Quick Start

```bash
# 交互式选择压缩模式 / Interactive mode selection
python3 compress_pdf.py report.pdf

# 直接指定模式 / Specify mode directly
python3 compress_pdf.py report.pdf --mode balanced
```

---

## 用法 / Usage

### 单文件 / Single File

```bash
python3 compress_pdf.py [OPTIONS] INPUT_PDF [OUTPUT_PDF]
```

### 参数 / Arguments

| 参数 / Argument | 说明 / Description |
| --- | --- |
| `INPUT_PDF` | 输入 PDF 文件路径 / Input PDF file path |
| `OUTPUT_PDF` | 输出路径（可选）/ Output path (optional) — defaults to `{name}-compressed.pdf` in the same directory |

### 选项 / Options

| 选项 / Option | 说明 / Description |
| --- | --- |
| `-m, --mode` | 压缩模式（不传时进入交互式菜单）/ Compression mode (omit to get interactive menu) |
| `--list-modes` | 列出所有模式说明 / List all available modes |
| `-h, --help` | 显示帮助 / Show help |

### 批量压缩 / Batch Compression

```bash
python3 compress_pdf_batch.py [OPTIONS] FILE_OR_DIR [MORE_FILES_OR_DIRS]
```

| 选项 / Option | 说明 / Description |
| --- | --- |
| `-m, --mode` | 压缩模式（必填）/ Compression mode (required) |
| `--recursive` | 递归处理子目录 / Recurse into subdirectories |

---

## 压缩模式 / Compression Modes

| 模式 / Mode | 分辨率 / DPI | JPEG 质量 / Quality | 说明 / Description |
| --- | --- | --- | --- |
| `high` | 300 DPI | 85 | 高质量存档，接近第三方工具效果 / High quality, suitable for archiving |
| `balanced` | 200 DPI | 80 | 均衡压缩，日常分享首选 / Balanced, good for everyday sharing |
| `extreme` | 150 DPI | 75 | 最大压缩率，适合邮件传输 / Maximum compression, best for email/transfer |
| `lossless` | 不降采样 / No downsampling | 无损 / Lossless | 仅优化结构，不影响图片质量（使用 qpdf）/ Structure-only optimization, no image quality loss |

---

## 示例 / Examples

```bash
# 交互式选择模式，输出 report-compressed.pdf / Interactive mode selection
python3 compress_pdf.py report.pdf

# 均衡模式 / Balanced compression
python3 compress_pdf.py report.pdf --mode balanced

# 指定输出路径 / Custom output path
python3 compress_pdf.py report.pdf output/small.pdf

# 极限压缩 / Maximum compression
python3 compress_pdf.py --mode extreme report.pdf

# 无损结构优化 / Lossless structural optimization
python3 compress_pdf.py --mode lossless report.pdf

# 查看所有模式 / List all modes
python3 compress_pdf.py --list-modes

# 批量压缩多个文件 / Batch compress multiple files
python3 compress_pdf_batch.py a.pdf b.pdf --mode balanced

# 压缩整个目录 / Compress an entire directory
python3 compress_pdf_batch.py ./docs --mode extreme

# 递归压缩目录和子目录 / Recursively compress directory
python3 compress_pdf_batch.py ./docs --mode high --recursive
```

---

## 输出文件规则 / Output File Rules

- 默认输出到源文件所在目录 / Output is placed in the same directory as the source file
- 默认文件名：`原文件名-compressed.pdf` / Default name: `{original}-compressed.pdf`
- 同名文件已存在时，自动追加序号：`-compressed-2.pdf`、`-compressed-3.pdf` …  
  On collision, a numeric suffix is appended automatically — existing files are never overwritten
- 批量模式自动跳过已生成的压缩结果，避免二次压缩  
  Batch mode skips previously generated `*-compressed*.pdf` files to prevent double-compression

---

## 分发 / Distribution

`dist/compress-pdf/` 目录是可直接交付给客户的独立包，包含所有必要文件：  
The `dist/compress-pdf/` directory is a self-contained package ready for distribution:

```text
dist/compress-pdf/
├── compress_pdf.py        # 单文件压缩入口 / Single-file compressor
├── compress_pdf_batch.py  # 批量压缩入口 / Batch compressor
├── requirements.txt       # Python 依赖 / Python dependencies
└── SKILL.md               # Skill 定义 / Skill definition
```

- skill 支持批量压缩多个文件或整个目录

## 参考数据

以 21 MB 的扫描版 PDF（15 页）为例：

| 模式 | 输出大小 | 压缩率 |
| --- | --- | --- |
| `lossless` | ~9 MB | ~57% |
| `high` | ~2 MB | ~90% |
| `balanced` | ~1.3 MB | ~94% |
| `extreme` | ~1.1 MB | ~95% |

## Shell 版本

如不需要 Python 环境，可直接使用同目录下的 `compress_pdf.sh`：

```bash
./compress_pdf.sh -m high input.pdf output.pdf
```
