from docx import Document as DocxDocument

from app.integrations.document_extractor import DocumentTextExtractor


def test_extracts_and_normalizes_plain_text(tmp_path) -> None:
    path = tmp_path / "resume.txt"
    path.write_text("  Backend Engineer  \n\n Python and FastAPI \n", encoding="utf-8")

    text = DocumentTextExtractor().extract(path, "text/plain")

    assert text == "Backend Engineer\nPython and FastAPI"


def test_extracts_paragraphs_and_tables_from_docx(tmp_path) -> None:
    path = tmp_path / "resume.docx"
    document = DocxDocument()
    document.add_paragraph("Backend Engineer")
    table = document.add_table(rows=1, cols=2)
    table.cell(0, 0).text = "Python"
    table.cell(0, 1).text = "FastAPI"
    document.save(path)

    text = DocumentTextExtractor().extract(
        path,
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )

    assert text == "Backend Engineer\nPython | FastAPI"
