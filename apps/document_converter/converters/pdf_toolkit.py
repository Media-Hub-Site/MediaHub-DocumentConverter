import os
import fitz  # PyMuPDF


class PDFToolkit:
    """Herramientas profesionales para manipulación de PDFs: Unir, Dividir y Extraer."""

    @staticmethod
    def merge_pdfs(file_paths: list[str], output_path: str) -> str:
        """Une múltiples archivos PDF en un solo documento."""
        if not file_paths:
            raise ValueError("No se seleccionó ningún archivo para unir.")

        doc_out = fitz.open()
        total_pages = 0

        for path in file_paths:
            if not os.path.exists(path):
                continue
            with fitz.open(path) as doc_in:
                doc_out.insert_pdf(doc_in)
                total_pages += len(doc_in)

        doc_out.save(output_path, deflate=True, garbage=3)
        doc_out.close()
        return f"✅ Se unieron {len(file_paths)} documentos con éxito ({total_pages} páginas totales)."

    @staticmethod
    def parse_page_range(range_str: str, max_pages: int) -> list[int]:
        """
        Parsea un string de rango estilo '1-3, 5, 8-10' a lista de índices 0-based.
        Valida que estén dentro de 1..max_pages.
        """
        pages = set()
        parts = [p.strip() for p in range_str.split(",") if p.strip()]

        for part in parts:
            if "-" in part:
                tokens = part.split("-")
                if len(tokens) == 2 and tokens[0].isdigit() and tokens[1].isdigit():
                    start, end = int(tokens[0]), int(tokens[1])
                    if start > end:
                        start, end = end, start
                    for p in range(start, end + 1):
                        if 1 <= p <= max_pages:
                            pages.add(p - 1)
            elif part.isdigit():
                p = int(part)
                if 1 <= p <= max_pages:
                    pages.add(p - 1)

        return sorted(list(pages))

    @staticmethod
    def split_pdf_by_range(input_path: str, output_path: str, page_range_str: str) -> str:
        """Extrae páginas específicas de un PDF a un nuevo archivo."""
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Archivo no encontrado: {input_path}")

        with fitz.open(input_path) as doc_in:
            total = len(doc_in)
            selected_indices = PDFToolkit.parse_page_range(page_range_str, total)
            if not selected_indices:
                raise ValueError(
                    f"Rango de páginas inválido o fuera de rango (el documento tiene {total} páginas)."
                )

            doc_out = fitz.open()
            for idx in selected_indices:
                doc_out.insert_pdf(doc_in, from_page=idx, to_page=idx)

            doc_out.save(output_path, deflate=True, garbage=3)
            doc_out.close()

            return f"✅ Se extrajeron {len(selected_indices)} páginas con éxito."

    @staticmethod
    def split_pdf_each_page(input_path: str, output_dir: str) -> list[str]:
        """Divide un PDF en un archivo por cada página individual."""
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Archivo no encontrado: {input_path}")

        os.makedirs(output_dir, exist_ok=True)
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        created_files = []

        with fitz.open(input_path) as doc_in:
            total = len(doc_in)
            for idx in range(total):
                page_doc = fitz.open()
                page_doc.insert_pdf(doc_in, from_page=idx, to_page=idx)
                out_file = os.path.join(output_dir, f"{base_name}_pag_{idx + 1:03d}.pdf")
                page_doc.save(out_file, deflate=True)
                page_doc.close()
                created_files.append(out_file)

        return created_files
