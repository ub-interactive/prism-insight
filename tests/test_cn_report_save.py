from pathlib import Path
from unittest.mock import patch

from prism.reporting.report_generator import save_cn_pdf_report, save_cn_report


def test_save_cn_report_writes_markdown(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "prism.reporting.report_generator.US_REPORTS_DIR",
        tmp_path,
    )
    content = "# Test Report\n\nBody"
    path = save_cn_report("600519", "贵州茅台", content)
    assert path.exists()
    assert path.read_text(encoding="utf-8") == content
    assert path.name.startswith("600519_")


@patch("prism.reporting.pdf_converter.markdown_to_pdf")
def test_save_cn_pdf_report_calls_converter(mock_markdown_to_pdf, tmp_path, monkeypatch):
    monkeypatch.setattr(
        "prism.reporting.report_generator.US_PDF_REPORTS_DIR",
        tmp_path,
    )
    md_path = tmp_path / "600519_test_analysis.md"
    md_path.write_text("# Test", encoding="utf-8")

    pdf_path = save_cn_pdf_report("600519", "贵州茅台", md_path)

    assert pdf_path.parent == tmp_path
    assert pdf_path.suffix == ".pdf"
    mock_markdown_to_pdf.assert_called_once()
