import io
import zipfile

from docx import Document as DocxDocument
from docx.table import Table
from docx.text.paragraph import Paragraph
from pypdf import PdfReader

MAX_DOCUMENT_PAGES = 200
MAX_EXTRACTED_CHARACTERS = 500_000
MAX_DOCX_MEMBERS = 2_000
MAX_DOCX_UNCOMPRESSED_BYTES = 25 * 1024 * 1024


class DocumentExtractionError(ValueError):
    """Raised when usable text cannot be extracted from a document."""


class DocumentTextExtractor:
    """Extract plain text from the document formats accepted by CareerOS."""

    def extract(self, data: bytes, content_type: str) -> str:
        """Read text from document bytes.

        Bytes rather than a path, because a deployed CareerOS keeps documents in
        object storage and never has them on a local filesystem.
        """
        try:
            if content_type == "application/pdf":
                text = self._extract_pdf(data)
            elif content_type == (
                "application/vnd.openxmlformats-officedocument."
                "wordprocessingml.document"
            ):
                text = self._extract_docx(data)
            elif content_type == "text/plain":
                text = data.decode("utf-8-sig")
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
        if len(normalized_text) > MAX_EXTRACTED_CHARACTERS:
            raise DocumentExtractionError(
                "The document contains too much text to process safely."
            )
        return normalized_text

    @staticmethod
    def _extract_pdf(data: bytes) -> str:
        reader = PdfReader(io.BytesIO(data))
        if len(reader.pages) > MAX_DOCUMENT_PAGES:
            raise DocumentExtractionError(
                f"PDFs may contain at most {MAX_DOCUMENT_PAGES} pages."
            )
        return "\n\n".join(page.extract_text() or "" for page in reader.pages)

    @staticmethod
    def _extract_docx(data: bytes) -> str:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            members = archive.infolist()
            if (
                len(members) > MAX_DOCX_MEMBERS
                or sum(member.file_size for member in members)
                > MAX_DOCX_UNCOMPRESSED_BYTES
            ):
                raise DocumentExtractionError(
                    "The DOCX expands beyond the safe processing limit."
                )
        document = DocxDocument(io.BytesIO(data))
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
