import os
import sys
import time

class DocumentFormats:
    @staticmethod
    def convertir(origen_path: str, destino_path: str, from_ext: str, to_ext: str) -> str:
        """
        Enruta la conversión a la función correspondiente según el formato origen y destino.
        """
        origen_path = os.path.abspath(origen_path)
        destino_path = os.path.abspath(destino_path)
        from_ext = from_ext.lower().replace(".", "")
        to_ext = to_ext.lower().replace(".", "")
        
        try:
            if from_ext in ("jpg", "jpeg", "png", "bmp", "webp") and to_ext == "pdf":
                return DocumentFormats.image_to_pdf(origen_path, destino_path)
            elif from_ext == "pdf" and to_ext in ("jpg", "jpeg", "png"):
                return DocumentFormats.pdf_to_images(origen_path, destino_path, to_ext)
            elif from_ext == "pdf" and to_ext == "docx":
                return DocumentFormats.pdf_to_word(origen_path, destino_path)
            elif from_ext in ("docx", "doc") and to_ext == "pdf":
                return DocumentFormats.word_to_pdf(origen_path, destino_path)
            elif from_ext in ("xlsx", "xls") and to_ext == "pdf":
                return DocumentFormats.excel_to_pdf(origen_path, destino_path)
            elif from_ext in ("pptx", "ppt") and to_ext == "pdf":
                return DocumentFormats.powerpoint_to_pdf(origen_path, destino_path)
            elif from_ext == "pdf" and to_ext in ("xlsx", "xls", "csv"):
                return DocumentFormats.pdf_to_excel(origen_path, destino_path)
            elif from_ext == "pdf" and to_ext in ("pptx", "ppt"):
                return DocumentFormats.pdf_to_powerpoint(origen_path, destino_path)
            elif from_ext in ("html", "htm") and to_ext == "pdf":
                return DocumentFormats.html_to_pdf(origen_path, destino_path)
            elif from_ext == "pdf" and to_ext == "pdf":
                # Optimización / PDF/A
                return DocumentFormats.optimize_pdf(origen_path, destino_path)
            else:
                return f"❌ Conversión de {from_ext.upper()} a {to_ext.upper()} no está soportada aún."
        except Exception as e:
            return f"❌ Error al convertir: {e}"

    @staticmethod
    def image_to_pdf(origen, destino):
        """Convierte imágenes (JPG, PNG, WebP, etc.) a PDF de alta fidelidad sin comprimir de más."""
        try:
            import fitz  # PyMuPDF
            doc = fitz.open()
            img = fitz.open(origen)
            rect = img[0].rect
            pdfbytes = img.convert_to_pdf()
            img.close()
            imgpdf = fitz.open("pdf", pdfbytes)
            page = doc.new_page(width=rect.width, height=rect.height)
            page.show_pdf_page(rect, imgpdf, 0)
            doc.save(destino)
            doc.close()
            return "✅ Imagen convertida a PDF exitosamente."
        except Exception:
            # Fallback a img2pdf
            try:
                import img2pdf
                from PIL import Image
                with Image.open(origen) as img:
                    img.verify()
                with open(destino, "wb") as f:
                    f.write(img2pdf.convert(origen))
                return "✅ Imagen convertida a PDF exitosamente."
            except Exception as e2:
                return f"❌ Error al convertir imagen a PDF: {e2}"

    @staticmethod
    def pdf_to_images(origen, destino, fmt="jpg"):
        """Convierte páginas de PDF a imágenes nítidas de 300 DPI."""
        try:
            import fitz
            doc = fitz.open(origen)
            num_pages = len(doc)
            if num_pages == 0:
                return "❌ El PDF está vacío."
                
            output_dir = os.path.dirname(destino)
            base_name = os.path.splitext(os.path.basename(destino))[0]
            
            target_dir = os.path.join(output_dir, base_name) if num_pages > 3 else output_dir
            os.makedirs(target_dir, exist_ok=True)
                
            for i in range(num_pages):
                page = doc.load_page(i)
                pix = page.get_pixmap(dpi=300)
                ext = "jpg" if fmt in ("jpg", "jpeg") else "png"
                if num_pages == 1:
                    file_path = os.path.join(target_dir, f"{base_name}.{ext}")
                else:
                    file_path = os.path.join(target_dir, f"{base_name}_pagina_{i+1}.{ext}")
                pix.save(file_path)
                
            doc.close()
            if num_pages > 1:
                return f"✅ {num_pages} páginas extraídas a {fmt.upper()} en '{os.path.basename(target_dir)}'."
            return f"✅ Página convertida a {fmt.upper()} exitosamente."
        except Exception as e:
            return f"❌ Error al extraer imágenes: {e}"

    @staticmethod
    def pdf_to_word(origen, destino):
        """Convierte PDF a Word (.docx) respetando tablas, texto editable y formato original."""
        from pdf2docx import Converter
        cv = None
        try:
            cv = Converter(origen)
            # convert con settings para mantener tablas limpias y sin forzar márgenes destructivos
            cv.convert(destino, start=0, end=None)
            return "✅ Archivo PDF convertido a Word exitosamente (Tablas y estructura preservadas)."
        except Exception as e:
            return f"❌ Error al convertir PDF a Word: {e}"
        finally:
            if cv is not None:
                try:
                    cv.close()
                except Exception:
                    pass

    @staticmethod
    def word_to_pdf(origen, destino):
        """Convierte Word (.docx) a PDF. Primero intenta Word nativo para 100% fidelidad."""
        # 1. Intentar Word nativo con comtypes
        try:
            import comtypes.client
            word = comtypes.client.CreateObject("Word.Application")
            try:
                word.Visible = False
                doc = word.Documents.Open(os.path.abspath(origen))
                # 17 = wdFormatPDF
                doc.SaveAs(os.path.abspath(destino), FileFormat=17)
                doc.Close()
                return "✅ Documento Word convertido a PDF con fidelidad nativa de Microsoft Word."
            finally:
                word.Quit()
        except Exception:
            pass

        # 2. Fallback a docx2pdf
        try:
            from docx2pdf import convert
            convert(origen, destino)
            return "✅ Documento Word convertido a PDF exitosamente."
        except Exception as e:
            return f"❌ Error al convertir Word a PDF: {e}"

    @staticmethod
    def excel_to_pdf(origen, destino):
        """Convierte hojas de cálculo Excel a PDF."""
        excel = None
        wb = None
        try:
            import comtypes.client
            excel = comtypes.client.CreateObject("Excel.Application")
            excel.Visible = False
            wb = excel.Workbooks.Open(os.path.abspath(origen))
            # 0 = xlTypePDF
            wb.ExportAsFixedFormat(0, os.path.abspath(destino))
            return "✅ Archivo Excel convertido a PDF exitosamente."
        except Exception as e:
            return f"❌ Error usando Excel: {e}. Asegúrate de tener MS Excel instalado."
        finally:
            if wb is not None:
                try:
                    wb.Close(False)
                except Exception:
                    pass
            if excel is not None:
                try:
                    excel.Quit()
                except Exception:
                    pass

    @staticmethod
    def powerpoint_to_pdf(origen, destino):
        """Convierte presentaciones PowerPoint a PDF."""
        powerpoint = None
        presentation = None
        try:
            import comtypes.client
            powerpoint = comtypes.client.CreateObject("Powerpoint.Application")
            presentation = powerpoint.Presentations.Open(os.path.abspath(origen), WithWindow=False)
            # 32 = ppFixedFormatTypePDF
            presentation.ExportAsFixedFormat(os.path.abspath(destino), 32)
            return "✅ Archivo PowerPoint convertido a PDF exitosamente."
        except Exception as e:
            return f"❌ Error usando PowerPoint: {e}. Asegúrate de tener MS PowerPoint instalado."
        finally:
            if presentation is not None:
                try:
                    presentation.Close()
                except Exception:
                    pass
            if powerpoint is not None:
                try:
                    powerpoint.Quit()
                except Exception:
                    pass

    @staticmethod
    def pdf_to_excel(origen, destino):
        """Extrae tablas de PDF a archivo Excel estructurado (.xlsx o .csv)."""
        # 1. Intentar con pdfplumber y pandas si están disponibles
        try:
            import pdfplumber
            import pandas as pd
            with pdfplumber.open(origen) as pdf:
                all_tables = []
                for page in pdf.pages:
                    tables = page.extract_tables()
                    for table in tables:
                        if not table or not table[0]:
                            continue
                        headers = table[0]
                        clean_headers = [str(h).strip() if h else f"Col_{j+1}" for j, h in enumerate(headers)]
                        data = []
                        for row in table[1:]:
                            clean_row = [str(cell).strip() if cell else "" for cell in row]
                            if len(clean_row) < len(clean_headers):
                                clean_row.extend([""] * (len(clean_headers) - len(clean_row)))
                            data.append(clean_row[:len(clean_headers)])
                        df = pd.DataFrame(data, columns=clean_headers)
                        all_tables.append(df)

                if all_tables:
                    with pd.ExcelWriter(destino) as writer:
                        for idx, df in enumerate(all_tables):
                            df.to_excel(writer, sheet_name=f"Tabla_{idx+1}", index=False)
                    return f"✅ Se extrajeron {len(all_tables)} tablas a Excel exitosamente."
        except Exception:
            pass

        # 2. Fallback ligero con PyMuPDF (fitz) - genera CSV o Excel básico sin necesidad de pandas
        try:
            import fitz
            doc = fitz.open(origen)
            rows = []
            for page in doc:
                tabs = page.find_tables()
                if tabs.tables:
                    for tab in tabs:
                        rows.extend(tab.extract())
            doc.close()

            if rows:
                import csv
                # Si destino pide xlsx pero no hay pandas, podemos escribir como CSV o con openpyxl
                csv_path = destino if destino.endswith(".csv") else os.path.splitext(destino)[0] + ".csv"
                with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
                    writer = csv.writer(f)
                    writer.writerows(rows)
                return f"✅ Tablas extraídas exitosamente como hoja de datos ({os.path.basename(csv_path)})."
            else:
                return "⚠️ No se detectaron tablas estructuradas en el PDF."
        except Exception as e:
            return f"❌ Error al extraer tablas a Excel: {e}"

    @staticmethod
    def pdf_to_powerpoint(origen, destino):
        """Convierte páginas de PDF en diapositivas de PowerPoint."""
        try:
            import fitz
            from pptx import Presentation
            import tempfile
            import shutil

            temp_dir = tempfile.mkdtemp(prefix="mediahub_pdf2ppt_")
            prs = Presentation()
            blank_layout = prs.slide_layouts[6]

            doc = fitz.open(origen)
            for i in range(len(doc)):
                page = doc.load_page(i)
                pix = page.get_pixmap(dpi=150)
                img_path = os.path.join(temp_dir, f"page_{i}.png")
                pix.save(img_path)

                slide = prs.slides.add_slide(blank_layout)
                slide.shapes.add_picture(img_path, 0, 0, width=prs.slide_width, height=prs.slide_height)

            prs.save(destino)
            doc.close()
            shutil.rmtree(temp_dir, ignore_errors=True)
            return "✅ Páginas del PDF convertidas a diapositivas PowerPoint exitosamente."
        except Exception as e:
            return f"❌ Error al convertir PDF a PowerPoint: {e}"

    @staticmethod
    def html_to_pdf(origen, destino):
        """Convierte archivos HTML a documento PDF."""
        try:
            from PyQt6.QtGui import QTextDocument
            from PyQt6.QtPrintSupport import QPrinter

            with open(origen, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()

            doc = QTextDocument()
            doc.setHtml(content)

            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(destino)

            doc.print(printer)
            if os.path.exists(destino):
                return "✅ Archivo HTML convertido a PDF exitosamente."
            return "❌ No se pudo generar el archivo PDF."
        except Exception as e:
            return f"❌ Error al convertir HTML a PDF: {e}"

    @staticmethod
    def optimize_pdf(origen, destino):
        """Optimiza y reduce el peso de un documento PDF limpiando streams obsoletos."""
        try:
            import fitz
            doc = fitz.open(origen)
            doc.save(destino, garbage=4, deflate=True, clean=True)
            doc.close()
            return "✅ Documento PDF optimizado y limpiado exitosamente."
        except Exception as e:
            return f"❌ Error optimizando PDF: {e}"
