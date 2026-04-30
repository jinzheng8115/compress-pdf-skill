import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

import compress_pdf
import compress_pdf_batch


MINIMAL_PDF = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Count 1 /Kids [3 0 R] >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 200 200] >>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \ntrailer\n<< /Root 1 0 R /Size 4 >>\nstartxref\n178\n%%EOF\n"


def write_pdf(path: Path) -> None:
    path.write_bytes(MINIMAL_PDF)


def fake_compress(_input_path: Path, output_path: Path, *_args: object) -> None:
    write_pdf(output_path)


class CompressPdfTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = CliRunner()

    def test_next_available_path_uses_incrementing_suffix(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "report.pdf"
            write_pdf(input_path)

            first_output = compress_pdf.default_output_path(input_path)
            write_pdf(first_output)
            write_pdf(first_output.with_name("report-compressed-2.pdf"))

            actual = compress_pdf.next_available_path(first_output)

            self.assertEqual(actual.name, "report-compressed-3.pdf")

    def test_cli_prompts_for_mode_when_not_provided(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "report.pdf"
            write_pdf(input_path)

            with patch.object(compress_pdf, "check_tool"), patch.object(
                compress_pdf,
                "compress_with_gs",
                side_effect=fake_compress,
            ):
                result = self.runner.invoke(compress_pdf.main, [str(input_path)], input="2\n")

            self.assertEqual(result.exit_code, 0, result.output)
            self.assertIn("balanced", result.output.lower())
            self.assertTrue((Path(temp_dir) / "report-compressed.pdf").exists())

    def test_cli_renames_default_output_when_file_exists(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "report.pdf"
            write_pdf(input_path)
            write_pdf(Path(temp_dir) / "report-compressed.pdf")

            with patch.object(compress_pdf, "check_tool"), patch.object(
                compress_pdf,
                "compress_with_gs",
                side_effect=fake_compress,
            ):
                result = self.runner.invoke(compress_pdf.main, [str(input_path), "--mode", "high"])

            self.assertEqual(result.exit_code, 0, result.output)
            self.assertIn("自动改名", result.output)
            self.assertTrue((Path(temp_dir) / "report-compressed-2.pdf").exists())

    def test_cli_renames_explicit_output_when_file_exists(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "report.pdf"
            output_path = Path(temp_dir) / "custom.pdf"
            write_pdf(input_path)
            write_pdf(output_path)

            with patch.object(compress_pdf, "check_tool"), patch.object(
                compress_pdf,
                "compress_with_gs",
                side_effect=fake_compress,
            ):
                result = self.runner.invoke(
                    compress_pdf.main,
                    [str(input_path), str(output_path), "--mode", "extreme"],
                )

            self.assertEqual(result.exit_code, 0, result.output)
            self.assertTrue((Path(temp_dir) / "custom-2.pdf").exists())

    def test_batch_collects_directory_pdfs_and_skips_generated_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            docs_dir = Path(temp_dir) / "docs"
            nested_dir = docs_dir / "nested"
            docs_dir.mkdir()
            nested_dir.mkdir()

            write_pdf(docs_dir / "report.pdf")
            write_pdf(docs_dir / "report-compressed.pdf")
            write_pdf(nested_dir / "scan.pdf")
            (docs_dir / "notes.txt").write_text("not a pdf", encoding="utf-8")

            flat_files = compress_pdf_batch.collect_input_pdfs((docs_dir,), recursive=False)
            recursive_files = compress_pdf_batch.collect_input_pdfs((docs_dir,), recursive=True)

            self.assertEqual([path.name for path in flat_files], ["report.pdf"])
            self.assertEqual([path.name for path in recursive_files], ["report.pdf", "scan.pdf"])

    def test_batch_cli_compresses_multiple_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            first_pdf = Path(temp_dir) / "first.pdf"
            second_pdf = Path(temp_dir) / "second.pdf"
            write_pdf(first_pdf)
            write_pdf(second_pdf)

            with patch.object(compress_pdf, "check_tool"), patch.object(
                compress_pdf,
                "compress_with_qpdf",
                side_effect=fake_compress,
            ):
                result = self.runner.invoke(
                    compress_pdf_batch.main,
                    [str(first_pdf), str(second_pdf), "--mode", "lossless"],
                )

            self.assertEqual(result.exit_code, 0, result.output)
            self.assertIn("成功处理 2 个 PDF", result.output)
            self.assertTrue((Path(temp_dir) / "first-compressed.pdf").exists())
            self.assertTrue((Path(temp_dir) / "second-compressed.pdf").exists())


if __name__ == "__main__":
    unittest.main()