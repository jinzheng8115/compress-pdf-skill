#!/usr/bin/env bash
# compress_pdf.sh — PDF 压缩脚本（基于 Ghostscript）
# 用法: ./compress_pdf.sh [选项] input.pdf [output.pdf]
#
# 质量模式:
#   high     — 300 DPI, JPEG q=85（默认，接近第三方工具效果）
#   balanced — 200 DPI, JPEG q=80（文件更小，质量可接受）
#   extreme  — 150 DPI, JPEG q=75（最大压缩）
#   lossless — 仅优化结构，不降采样图片（使用 qpdf）

set -euo pipefail

# ── 默认参数 ──────────────────────────────────────────────
MODE="high"
INPUT=""
OUTPUT=""

# ── 颜色输出 ──────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

usage() {
  cat <<EOF
用法: $(basename "$0") [选项] input.pdf [output.pdf]

选项:
  -m, --mode MODE    压缩模式: high | balanced | extreme | lossless
                     (默认: high)
  -h, --help         显示帮助

示例:
  $(basename "$0") input.pdf
  $(basename "$0") -m balanced input.pdf output.pdf
  $(basename "$0") --mode extreme big.pdf small.pdf
EOF
}

# ── 参数解析 ──────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    -m|--mode)
      MODE="$2"; shift 2 ;;
    -h|--help)
      usage; exit 0 ;;
    -*)
      echo -e "${RED}未知选项: $1${NC}" >&2; usage; exit 1 ;;
    *)
      if [[ -z "$INPUT" ]]; then
        INPUT="$1"
      elif [[ -z "$OUTPUT" ]]; then
        OUTPUT="$1"
      else
        echo -e "${RED}参数过多${NC}" >&2; usage; exit 1
      fi
      shift ;;
  esac
done

# ── 校验输入 ──────────────────────────────────────────────
if [[ -z "$INPUT" ]]; then
  echo -e "${RED}错误: 请指定输入文件${NC}" >&2; usage; exit 1
fi

if [[ ! -f "$INPUT" ]]; then
  echo -e "${RED}错误: 文件不存在: $INPUT${NC}" >&2; exit 1
fi

# 生成默认输出文件名
if [[ -z "$OUTPUT" ]]; then
  base="${INPUT%.pdf}"
  OUTPUT="${base}-compressed.pdf"
fi

# 检查输入输出是否相同
INPUT_ABS="$(cd "$(dirname "$INPUT")" && pwd)/$(basename "$INPUT")"
OUTPUT_ABS="$(cd "$(dirname "$OUTPUT" 2>/dev/null || echo "$(dirname "$OUTPUT")")" 2>/dev/null && pwd)/$(basename "$OUTPUT")" 2>/dev/null || OUTPUT_ABS="$OUTPUT"
if [[ "$INPUT_ABS" == "$OUTPUT_ABS" ]]; then
  echo -e "${RED}错误: 输入和输出文件不能相同${NC}" >&2; exit 1
fi

# ── 依赖检查 ──────────────────────────────────────────────
check_tool() {
  if ! command -v "$1" &>/dev/null; then
    echo -e "${RED}错误: 未找到 $1，请先安装: brew install $2${NC}" >&2
    exit 1
  fi
}

case "$MODE" in
  high|balanced|extreme)
    check_tool gs ghostscript ;;
  lossless)
    check_tool qpdf qpdf ;;
  *)
    echo -e "${RED}错误: 未知模式 '$MODE'，可选: high | balanced | extreme | lossless${NC}" >&2
    exit 1 ;;
esac

# ── 文件大小辅助函数 ──────────────────────────────────────
file_size_mb() {
  local size
  size=$(stat -f%z "$1" 2>/dev/null || stat -c%s "$1" 2>/dev/null)
  echo "scale=2; $size / 1048576" | bc
}

# ── 执行压缩 ──────────────────────────────────────────────
echo -e "${CYAN}=== PDF 压缩工具 ===${NC}"
echo -e "输入: ${INPUT}"
echo -e "输出: ${OUTPUT}"
echo -e "模式: ${YELLOW}${MODE}${NC}"
echo ""

INPUT_SIZE=$(file_size_mb "$INPUT")
echo -e "原始大小: ${INPUT_SIZE} MB"
echo ""

case "$MODE" in
  high)
    echo "使用 Ghostscript 压缩 (300 DPI, JPEG q=85)..."
    gs -sDEVICE=pdfwrite \
       -dCompatibilityLevel=1.5 \
       -dNOPAUSE -dQUIET -dBATCH \
       -dDetectDuplicateImages=true \
       -dCompressFonts=true \
       -dSubsetFonts=true \
       -dAutoFilterColorImages=false \
       -dAutoFilterGrayImages=false \
       -dColorImageFilter=/DCTEncode \
       -dGrayImageFilter=/DCTEncode \
       -dJPEGQ=85 \
       -dDownsampleColorImages=true \
       -dDownsampleGrayImages=true \
       -dDownsampleMonoImages=false \
       -dColorImageDownsampleType=/Bicubic \
       -dGrayImageDownsampleType=/Bicubic \
       -dColorImageResolution=300 \
       -dGrayImageResolution=300 \
       -sOutputFile="$OUTPUT" \
       "$INPUT"
    ;;

  balanced)
    echo "使用 Ghostscript 压缩 (200 DPI, JPEG q=80)..."
    gs -sDEVICE=pdfwrite \
       -dCompatibilityLevel=1.5 \
       -dNOPAUSE -dQUIET -dBATCH \
       -dDetectDuplicateImages=true \
       -dCompressFonts=true \
       -dSubsetFonts=true \
       -dAutoFilterColorImages=false \
       -dAutoFilterGrayImages=false \
       -dColorImageFilter=/DCTEncode \
       -dGrayImageFilter=/DCTEncode \
       -dJPEGQ=80 \
       -dDownsampleColorImages=true \
       -dDownsampleGrayImages=true \
       -dDownsampleMonoImages=false \
       -dColorImageDownsampleType=/Bicubic \
       -dGrayImageDownsampleType=/Bicubic \
       -dColorImageResolution=200 \
       -dGrayImageResolution=200 \
       -sOutputFile="$OUTPUT" \
       "$INPUT"
    ;;

  extreme)
    echo "使用 Ghostscript 压缩 (150 DPI, JPEG q=75)..."
    gs -sDEVICE=pdfwrite \
       -dCompatibilityLevel=1.5 \
       -dNOPAUSE -dQUIET -dBATCH \
       -dDetectDuplicateImages=true \
       -dCompressFonts=true \
       -dSubsetFonts=true \
       -dAutoFilterColorImages=false \
       -dAutoFilterGrayImages=false \
       -dColorImageFilter=/DCTEncode \
       -dGrayImageFilter=/DCTEncode \
       -dJPEGQ=75 \
       -dDownsampleColorImages=true \
       -dDownsampleGrayImages=true \
       -dDownsampleMonoImages=false \
       -dColorImageDownsampleType=/Bicubic \
       -dGrayImageDownsampleType=/Bicubic \
       -dColorImageResolution=150 \
       -dGrayImageResolution=150 \
       -sOutputFile="$OUTPUT" \
       "$INPUT"
    ;;

  lossless)
    echo "使用 qpdf 进行无损结构优化..."
    qpdf --linearize \
         --compress-streams=y \
         --object-streams=generate \
         --recompress-flate \
         --compression-level=9 \
         "$INPUT" "$OUTPUT"
    ;;
esac

# ── 结果报告 ──────────────────────────────────────────────
if [[ -f "$OUTPUT" ]]; then
  OUTPUT_SIZE=$(file_size_mb "$OUTPUT")
  RATIO=$(echo "scale=1; (1 - $OUTPUT_SIZE / $INPUT_SIZE) * 100" | bc)
  echo ""
  echo -e "${GREEN}✓ 压缩完成${NC}"
  echo -e "原始大小: ${INPUT_SIZE} MB"
  echo -e "压缩后:   ${OUTPUT_SIZE} MB"
  echo -e "压缩率:   ${RATIO}%"
  echo -e "输出文件: ${OUTPUT}"
else
  echo -e "${RED}✗ 压缩失败，未生成输出文件${NC}" >&2
  exit 1
fi
