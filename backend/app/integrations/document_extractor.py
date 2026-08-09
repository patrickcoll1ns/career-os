from pathlib import Path

from docx import Document as DocxDocument
from docx.table import Table
from docx.text.paragraph import Paragraph
from pypdf import PdfReader


class DocumentExtractionError(ValueError):
    """Raised when usable text cannot be extracted from a document."""


class DocumentTextExtractor:
    """Extract plain text from the document formats accepted by CareerOS."""

    def extract(self, path: Path, content_type: str) -> str:
        try:
            if content_type == "application/pdf":
                text = self._extract_pdf(path)
            elif content_type == (
                "application/vnd.openxmlformats-officedocument."
                "wordprocessingml.document"
            ):
                text = self._extract_docx(path)
            elif content_type == "text/plain":
                text = path.read_text(encoding="utf-8-sig")
            else:
                raise DocumentExtractionError("This document type is not supported.")
        except DocumentExtractionError:
            raise
        except Exception as error:
            raise DocumentExtractionError(
                "CareerOS could not read text from this document."
            ) from error

        normalized_text = self._normalize(text)
        if not normalized_text:
            raise DocumentExtractionError(
                "No readable text was found. Scanned PDFs are not supported yet."
            )
        return normalized_text

    @staticmethod
    def _extract_pdf(path: Path) -> str:
        reader = PdfReader(path)
        return "\n\n".join(page.extract_text() or "" for page in reader.pages)

    @staticmethod
    def _extract_docx(path: Path) -> str:
        document = DocxDocument(path)
        blocks: list[str] = []

        for block in document.iter_inner_content():
            if isinstance(block, Paragraph):
                blocks.append(block.text)
            elif isinstance(block, Table):
                for row in block.rows:
                    blocks.append(" | ".join(cell.text for cell in row.cells))

        return "\n".join(blocks)

    @staticmethod
    def _normalize(text: str) -> str:
        return "\n".join(line.strip() for line in text.splitlines() if line.strip())
