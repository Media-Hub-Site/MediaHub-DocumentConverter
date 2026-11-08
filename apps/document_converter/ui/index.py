import os
import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QMessageBox, QFrame, QFileDialog, QProgressBar, QButtonGroup
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QIcon, QPixmap

from apps.document_converter.ui.ui_theme import (
    get_app_colors,
    apply_window_theme,
    make_card_container,
)
from apps.document_converter.converters.conversion import DocumentFormats


# Mapeo de formatos soportados y sus opciones recomendadas
SUPPORTED_EXTS = {
    ".docx": ("Documento Word", "word.png", [("PDF", "pdf", True)]),
    ".doc":  ("Documento Word", "word.png", [("PDF", "pdf", True)]),
    ".xlsx": ("Hoja de Cálculo Excel", "excel.png", [("PDF", "pdf", True)]),
    ".xls":  ("Hoja de Cálculo Excel", "excel.png", [("PDF", "pdf", True)]),
    ".pptx": ("Presentación PowerPoint", "ppt.png", [("PDF", "pdf", True)]),
    ".ppt":  ("Presentación PowerPoint", "ppt.png", [("PDF", "pdf", True)]),
    ".jpg":  ("Imagen JPG", "jpg.png", [("PDF", "pdf", True)]),
    ".jpeg": ("Imagen JPEG", "jpg.png", [("PDF", "pdf", True)]),
    ".png":  ("Imagen PNG", "jpg.png", [("PDF", "pdf", True)]),
    ".html": ("Página Web HTML", "html.png", [("PDF", "pdf", True)]),
    ".htm":  ("Página Web HTML", "html.png", [("PDF", "pdf", True)]),
    ".pdf":  (
        "Documento PDF", "pdf.png",
        [
            ("Word (.docx)", "docx", True),
            ("Excel (.xlsx)", "xlsx", False),
            ("PowerPoint (.pptx)", "pptx", False),
            ("Imágenes JPG", "jpg", False),
            ("Optimizar PDF", "pdf", False),
        ]
    ),
}


class DocConvertThread(QThread):
    progress = pyqtSignal(int, str)
    finished_success = pyqtSignal(str, str)
    error = pyqtSignal(str)

    def __init__(self, input_path, output_path, from_ext, to_ext):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path
        self.from_ext = from_ext
        self.to_ext = to_ext

    def run(self):
        try:
            self.progress.emit(25, f"Procesando archivo {self.from_ext.upper()}...")
            res = DocumentFormats.convertir(
                self.input_path, self.output_path, self.from_ext, self.to_ext
            )
            self.progress.emit(85, "Finalizando exportación...")

            if str(res).startswith("✅") or str(res).startswith("⚠️"):
                self.progress.emit(100, "¡Conversión completada!")
                self.finished_success.emit(self.output_path, str(res))
            else:
                self.error.emit(str(res))
        except Exception as e:
            self.error.emit(str(e))


class DocumentLauncherWindow(QWidget):
    """Interfaz moderna Smart Dropzone para el Convertidor de Documentos."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Document Converter — Media Hub")
        self.resize(920, 680)
        self.setMinimumSize(850, 620)
        apply_window_theme(self)
        self._colors = get_app_colors()

        icon_path = self._get_asset_path(os.path.join("hub", "Media-Hub.ico"))
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.current_file = None
        self.selected_target_ext = "pdf"
        self.target_buttons = {}

        self.init_ui()

    def _get_asset_path(self, subpath: str) -> str:
        if getattr(sys, "frozen", False):
            base_dir = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
        else:
            base_dir = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..", "..", "..")
            )
        return os.path.join(base_dir, "assets", subpath)

    def init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(36, 28, 36, 28)
        root.setSpacing(16)

        card, layout = make_card_container()

        # Header
        header_row = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("DOCUMENT CONVERTER")
        title.setStyleSheet(f"font-size: 20pt; font-weight: 800; color: {self._colors['text_main']}; letter-spacing: 0.5px;")
        desc = QLabel("Arrastra cualquier documento. El conversor inteligente detectará las opciones de salida al instante.")
        desc.setStyleSheet(f"color: {self._colors['text_muted']}; font-size: 10.5pt;")
        title_box.addWidget(title)
        title_box.addWidget(desc)
        header_row.addLayout(title_box)
        header_row.addStretch()

        # Botón salir elegante en esquina superior
        exit_btn = QPushButton("🚪 Salir")
        exit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        exit_btn.setFixedHeight(34)
        exit_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {self._colors['text_muted']};
                padding: 4px 14px;
                border-radius: 8px;
                font-weight: 600;
                border: 1px solid {self._colors['border']};
            }}
            QPushButton:hover {{
                background-color: rgba(235, 87, 87, 0.15);
                color: #FF5A5A;
                border-color: rgba(235, 87, 87, 0.4);
            }}
        """)
        exit_btn.clicked.connect(self.close)
        header_row.addWidget(exit_btn)
        layout.addLayout(header_row)
        layout.addSpacing(10)

        # ── Smart Drop Zone ───────────────────────────────────────────────────
        self.drop_zone = QFrame()
        self.drop_zone.setAcceptDrops(True)
        self.drop_zone.setFixedHeight(180)
        self.drop_zone.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors['bg']};
                border: 2.5px dashed {self._colors['border']};
                border-radius: 16px;
            }}
            QFrame:hover {{
                border-color: {self._colors['accent']};
                background-color: {self._colors['accent_soft']};
            }}
        """)

        drop_layout = QVBoxLayout(self.drop_zone)
        drop_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        drop_layout.setSpacing(6)

        self.drop_icon = QLabel("📄")
        self.drop_icon.setStyleSheet("font-size: 32pt; background: transparent;")
        self.drop_title = QLabel("Arrastra tu documento aquí o haz clic para explorar")
        self.drop_title.setStyleSheet(f"color: {self._colors['text_main']}; font-size: 13pt; font-weight: 700; background: transparent;")
        self.drop_subtitle = QLabel("Soporta Word (DOCX/DOC), Excel (XLSX), PowerPoint (PPTX), PDF, JPG, PNG, HTML")
        self.drop_subtitle.setStyleSheet(f"color: {self._colors['text_muted']}; font-size: 9.5pt; background: transparent;")

        drop_layout.addWidget(self.drop_icon, alignment=Qt.AlignmentFlag.AlignCenter)
        drop_layout.addWidget(self.drop_title, alignment=Qt.AlignmentFlag.AlignCenter)
        drop_layout.addWidget(self.drop_subtitle, alignment=Qt.AlignmentFlag.AlignCenter)

        self.drop_zone.mousePressEvent = lambda e: self.select_file()
        self.drop_zone.dragEnterEvent = self.drag_enter_event
        self.drop_zone.dropEvent = self.drop_event

        layout.addWidget(self.drop_zone)
        layout.addSpacing(8)

        # ── Panel de Opciones de Salida Inteligente ───────────────────────────
        self.action_panel = QFrame()
        self.action_panel.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors['bg']};
                border-radius: 14px;
                padding: 14px;
            }}
        """)
        action_layout = QVBoxLayout(self.action_panel)
        action_layout.setSpacing(10)

        self.lbl_detected = QLabel("💡 Selecciona o arrastra un archivo para ver los formatos disponibles")
        self.lbl_detected.setStyleSheet(f"color: {self._colors['text_muted']}; font-weight: 700; font-size: 11pt;")
        action_layout.addWidget(self.lbl_detected)

        # Botones de formato de destino (Pills)
        self.pills_layout = QHBoxLayout()
        self.pills_layout.setSpacing(10)
        self.btn_group = QButtonGroup(self)
        self.btn_group.setExclusive(True)
        action_layout.addLayout(self.pills_layout)

        layout.addWidget(self.action_panel)
        layout.addSpacing(10)

        # ── Barra de Progreso y Estado ────────────────────────────────────────
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedHeight(12)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background: {self._colors['bg']};
                border-radius: 6px;
                border: 1px solid {self._colors['border']};
            }}
            QProgressBar::chunk {{
                background: {self._colors['accent']};
                border-radius: 5px;
            }}
        """)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet(f"color: {self._colors['text_muted']}; font-weight: 600; font-size: 10pt;")
        layout.addWidget(self.status_label)

        # ── Botón de Acción Principal ─────────────────────────────────────────
        bottom_row = QHBoxLayout()
        bottom_row.addStretch()

        self.btn_convert = QPushButton("🚀 Convertir Documento")
        self.btn_convert.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_convert.setFixedHeight(48)
        self.btn_convert.setFixedWidth(240)
        self.btn_convert.setEnabled(False)
        self.btn_convert.setStyleSheet(f"""
            QPushButton {{
                background-color: {self._colors['accent']};
                color: #FFFFFF;
                border: none;
                border-radius: 12px;
                font-size: 11.5pt;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background-color: {self._colors['accent_hover']};
            }}
            QPushButton:disabled {{
                background-color: {self._colors['border']};
                color: {self._colors['text_muted']};
            }}
        """)
        self.btn_convert.clicked.connect(self.start_conversion)
        bottom_row.addWidget(self.btn_convert)
        bottom_row.addStretch()

        layout.addLayout(bottom_row)
        root.addWidget(card)

    def drag_enter_event(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                path = urls[0].toLocalFile()
                ext = os.path.splitext(path)[1].lower()
                if ext in SUPPORTED_EXTS:
                    event.acceptProposedAction()

    def drop_event(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            self._set_file(path)

    def select_file(self):
        filters = "Documentos (*.docx *.doc *.xlsx *.xls *.pptx *.ppt *.pdf *.jpg *.jpeg *.png *.html *.htm)"
        path, _ = QFileDialog.getOpenFileName(self, "Seleccionar Documento", "", filters)
        if path:
            self._set_file(path)

    def _set_file(self, file_path):
        self.current_file = file_path
        name = os.path.basename(file_path)
        ext = os.path.splitext(file_path)[1].lower()

        info = SUPPORTED_EXTS.get(ext)
        if not info:
            QMessageBox.warning(self, "Formato No Soportado", f"El formato '{ext}' no está soportado.")
            return

        doc_type, icon_name, targets = info

        # Actualizar Dropzone visualmente
        self.drop_icon.setText("📑")
        self.drop_title.setText(f"{name}")
        size_kb = os.path.getsize(file_path) / 1024
        self.drop_subtitle.setText(f"{doc_type} • {size_kb:.1f} KB")

        # Actualizar opciones de salida dinámicamente
        self.lbl_detected.setText(f"🎯 Archivo detectado: {doc_type}. Elige el formato de salida:")

        # Limpiar píldoras anteriores
        for btn in self.target_buttons.values():
            self.pills_layout.removeWidget(btn)
            btn.deleteLater()
        self.target_buttons.clear()

        # Crear nuevas píldoras según el archivo
        default_ext = None
        for label, tgt_ext, is_default in targets:
            pill = QPushButton(label)
            pill.setCheckable(True)
            pill.setCursor(Qt.CursorShape.PointingHandCursor)
            pill.setFixedHeight(38)
            pill.setStyleSheet(f"""
                QPushButton {{
                    background-color: {self._colors['card']};
                    color: {self._colors['text_main']};
                    border: 1px solid {self._colors['border']};
                    border-radius: 9px;
                    padding: 6px 16px;
                    font-size: 10pt;
                    font-weight: 600;
                }}
                QPushButton:hover {{
                    border-color: {self._colors['accent']};
                }}
                QPushButton:checked {{
                    background-color: {self._colors['accent']};
                    color: #FFFFFF;
                    font-weight: 700;
                    border: none;
                }}
            """)
            pill.clicked.connect(lambda checked, t=tgt_ext: self._select_target(t))
            self.btn_group.addButton(pill)
            self.pills_layout.addWidget(pill)
            self.target_buttons[tgt_ext] = pill

            if is_default or default_ext is None:
                default_ext = tgt_ext

        if default_ext and default_ext in self.target_buttons:
            self.target_buttons[default_ext].setChecked(True)
            self.selected_target_ext = default_ext

        self.btn_convert.setEnabled(True)
        self.status_label.setText("")

    def _select_target(self, ext):
        self.selected_target_ext = ext

    def start_conversion(self):
        if not self.current_file or not os.path.exists(self.current_file):
            return

        base, in_ext = os.path.splitext(self.current_file)
        out_ext = self.selected_target_ext.lower().replace(".", "")

        default_name = f"{base}.{out_ext}"
        filter_str = f"Archivo {out_ext.upper()} (*.{out_ext})"

        output_path, _ = QFileDialog.getSaveFileName(
            self, "Guardar Documento Convertido", default_name, filter_str
        )
        if not output_path:
            return

        self.btn_convert.setEnabled(False)
        self.drop_zone.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(15)

        clean_in_ext = in_ext.lower().replace(".", "")
        self.worker = DocConvertThread(self.current_file, output_path, clean_in_ext, out_ext)
        self.worker.progress.connect(self._on_progress)
        self.worker.finished_success.connect(self._on_success)
        self.worker.error.connect(self._on_error)
        self.worker.start()

    def _on_progress(self, val, msg):
        self.progress_bar.setValue(val)
        self.status_label.setText(msg)

    def _on_success(self, output_path, message):
        self.btn_convert.setEnabled(True)
        self.drop_zone.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText("✅ Conversión completada exitosamente")
        QMessageBox.information(
            self, "Conversión Completada",
            f"{message}\n\nGuardado en:\n{output_path}"
        )

    def _on_error(self, err):
        self.btn_convert.setEnabled(True)
        self.drop_zone.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText("❌ Error al convertir documento")
        QMessageBox.critical(self, "Error en Conversión", f"No se pudo completar la operación:\n\n{err}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DocumentLauncherWindow()
    window.show()
    sys.exit(app.exec())
