from pathlib import Path

import fitz
from docx import Document


class DocumentParser:

    SUPPORTED_EXTENSIONS = [
        ".pdf",
        ".docx",
        ".txt"
    ]

    @staticmethod
    def parse(file_path: str) -> str:

        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(
                f"{file_path} does not exist."
            )

        suffix = file_path.suffix.lower()

        if suffix not in DocumentParser.SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported file type: {suffix}"
            )

        if suffix == ".pdf":
            return DocumentParser._parse_pdf(file_path)

        if suffix == ".docx":
            return DocumentParser._parse_docx(file_path)

        if suffix == ".txt":
            return DocumentParser._parse_txt(file_path)

        raise ValueError("Unsupported file format")

    @staticmethod
    def _parse_pdf(file_path: Path) -> str:

        text = []

        with fitz.open(file_path) as pdf:

            for page in pdf:
                page_text = page.get_text()

                if page_text:
                    text.append(page_text)

        return "\n".join(text)

    @staticmethod
    def _parse_docx(file_path: Path) -> str:

        doc = Document(file_path)

        paragraphs = []

        for para in doc.paragraphs:

            if para.text.strip():
                paragraphs.append(
                    para.text.strip()
                )

        return "\n".join(paragraphs)

    @staticmethod
    def _parse_txt(file_path: Path) -> str:

        return file_path.read_text(
            encoding="utf-8"
        )