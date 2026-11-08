import os
import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QMessageBox, QFrame, QFileDialog, QProgressBar, QButtonGroup, QTabWidget,
    QListWidget, QListWidgetItem, QLineEdit, QRadioButton
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QIcon

from apps.document_converter.ui.ui_theme import (
    get_app_colors,
    apply_window_theme,
    make_card_container,
)
from apps.document_converter.converters.conversion import DocumentFormats
from apps.document_converter.converters.pdf_toolkit import PDFToolkit


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
    """Suite Integral de Documentos y PDF: Conversión, Unión y División Inteligente."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Document Converter & PDF Studio — Media Hub")
        self.resize(980, 700)
        self.setMinimumSize(880, 640)
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
        root.setContentsMargins(28, 20, 28, 20)
        root.setSpacing(12)

        card, layout = make_card_container()

        # Header
        header_row = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("DOCUMENT & PDF STUDIO")
        title.setStyleSheet(f"font-size: 20pt; font-weight: 800; color: {self._colors['text_main']}; letter-spacing: 0.5px;")
        desc = QLabel("Convierte entre Word, Excel, PowerPoint y PDF, o utiliza las herramientas rápidas de Unión y División.")
        desc.setStyleSheet(f"color: {self._colors['text_muted']}; font-size: 10.5pt;")
        title_box.addWidget(title)
        title_box.addWidget(desc)
        header_row.addLayout(title_box)
        header_row.addStretch()

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
        layout.addSpacing(6)

        # Tabs: Conversor Inteligente / Unir PDFs / Dividir PDF
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {self._colors['border']};
                border-radius: 12px;
                background-color: {self._colors['bg']};
                padding: 16px;
            }}
            QTabBar::tab {{
                background: transparent;
                color: {self._colors['text_muted']};
                padding: 8px 18px;
                margin-right: 6px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-weight: 700;
                font-size: 10.5pt;
            }}
            QTabBar::tab:selected {{
                background-color: {self._colors['accent']};
                color: #FFFFFF;
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {self._colors['accent_soft']};
                color: {self._colors['accent']};
            }}
        """)

        # Tab 1: Conversor
        tab_convert = self._create_convert_tab()
        # Tab 2: Unir PDFs
        tab_merge = self._create_merge_tab()
        # Tab 3: Dividir PDF
        tab_split = self._create_split_tab()

        self.tabs.addTab(tab_convert, "⚡ Conversor Universal")
        self.tabs.addTab(tab_merge, "📑 Unir PDFs (Merge)")
        self.tabs.addTab(tab_split, "✂️ Dividir / Extraer (Split)")

        layout.addWidget(self.tabs)
        root.addWidget(card)

    def _create_convert_tab(self) -> QWidget:
        widget = QWidget()
        vbox = QVBoxLayout(widget)
        vbox.setContentsMargins(10, 10, 10, 10)
        vbox.setSpacing(12)

        # Smart Dropzone
        self.drop_zone = QFrame()
        self.drop_zone.setAcceptDrops(True)
        self.drop_zone.setFixedHeight(160)
        self.drop_zone.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors['card']};
                border: 2px dashed {self._colors['border']};
                border-radius: 14px;
            }}
            QFrame:hover {{
                border-color: {self._colors['accent']};
                background-color: {self._colors['accent_soft']};
            }}
        """)
        drop_layout = QVBoxLayout(self.drop_zone)
        drop_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        drop_layout.setSpacing(4)

        self.drop_icon = QLabel("📄")
        self.drop_icon.setStyleSheet("font-size: 28pt; background: transparent;")
        self.drop_title = QLabel("Arrastra tu documento aquí o haz clic para explorar")
        self.drop_title.setStyleSheet(f"color: {self._colors['text_main']}; font-size: 12.5pt; font-weight: 700; background: transparent;")
        self.drop_subtitle = QLabel("Soporta Word (DOCX/DOC), Excel (XLSX), PowerPoint (PPTX), PDF, JPG, PNG, HTML")
        self.drop_subtitle.setStyleSheet(f"color: {self._colors['text_muted']}; font-size: 9pt; background: transparent;")

        drop_layout.addWidget(self.drop_icon, alignment=Qt.AlignmentFlag.AlignCenter)
        drop_layout.addWidget(self.drop_title, alignment=Qt.AlignmentFlag.AlignCenter)
        drop_layout.addWidget(self.drop_subtitle, alignment=Qt.AlignmentFlag.AlignCenter)

        self.drop_zone.mousePressEvent = lambda e: self.select_file()
        self.drop_zone.dragEnterEvent = self.drag_enter_event
        self.drop_zone.dropEvent = self.drop_event
        vbox.addWidget(self.drop_zone)

        # Action Panel
        self.action_panel = QFrame()
        self.action_panel.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors['card']};
                border-radius: 12px;
                padding: 10px;
                border: 1px solid {self._colors['border']};
            }}
        """)
        action_layout = QVBoxLayout(self.action_panel)
        action_layout.setSpacing(8)

        self.lbl_detected = QLabel("💡 Selecciona o arrastra un archivo para ver los formatos disponibles")
        self.lbl_detected.setStyleSheet(f"color: {self._colors['text_muted']}; font-weight: 700; font-size: 10pt;")
        action_layout.addWidget(self.lbl_detected)

        self.pills_layout = QHBoxLayout()
        self.pills_layout.setSpacing(10)
        self.btn_group = QButtonGroup(self)
        self.btn_group.setExclusive(True)
        action_layout.addLayout(self.pills_layout)
        vbox.addWidget(self.action_panel)

        # Barra y progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedHeight(10)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background: {self._colors['card']};
                border-radius: 5px;
                border: 1px solid {self._colors['border']};
            }}
            QProgressBar::chunk {{
                background: {self._colors['accent']};
                border-radius: 4px;
            }}
        """)
        vbox.addWidget(self.progress_bar)

        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet(f"color: {self._colors['text_muted']}; font-weight: 600; font-size: 9.5pt;")
        vbox.addWidget(self.status_label)

        bottom_row = QHBoxLayout()
        bottom_row.addStretch()
        self.btn_convert = QPushButton("🚀 Convertir Documento")
        self.btn_convert.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_convert.setFixedHeight(44)
        self.btn_convert.setFixedWidth(230)
        self.btn_convert.setEnabled(False)
        self.btn_convert.setStyleSheet(f"""
            QPushButton {{
                background-color: {self._colors['accent']};
                color: #FFFFFF;
                border: none;
                border-radius: 10px;
                font-size: 11pt;
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
        vbox.addLayout(bottom_row)

        return widget

    def _create_merge_tab(self) -> QWidget:
        widget = QWidget()
        vbox = QVBoxLayout(widget)
        vbox.setContentsMargins(10, 10, 10, 10)
        vbox.setSpacing(10)

        info = QLabel("Une múltiples archivos PDF en un solo documento en el orden que tú decidas:")
        info.setStyleSheet(f"color: {self._colors['text_muted']}; font-size: 10pt; font-weight: 600;")
        vbox.addWidget(info)

        # Lista de archivos
        self.merge_list = QListWidget()
        self.merge_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {self._colors['card']};
                border: 1px solid {self._colors['border']};
                border-radius: 10px;
                color: {self._colors['text_main']};
                font-size: 10pt;
                padding: 6px;
            }}
            QListWidget::item {{
                padding: 6px 10px;
                border-radius: 6px;
            }}
            QListWidget::item:selected {{
                background-color: {self._colors['accent_soft']};
                color: {self._colors['accent']};
                font-weight: 700;
            }}
        """)
        vbox.addWidget(self.merge_list)

        # Botonera de control de lista
        btn_row = QHBoxLayout()
        add_btn = QPushButton("➕ Agregar PDFs")
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.setStyleSheet(self._btn_secondary_style())
        add_btn.clicked.connect(self._add_merge_files)

        up_btn = QPushButton("⬆️ Subir")
        up_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        up_btn.setStyleSheet(self._btn_secondary_style())
        up_btn.clicked.connect(self._move_merge_item_up)

        down_btn = QPushButton("⬇️ Bajar")
        down_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        down_btn.setStyleSheet(self._btn_secondary_style())
        down_btn.clicked.connect(self._move_merge_item_down)

        del_btn = QPushButton("🗑️ Eliminar")
        del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        del_btn.setStyleSheet(self._btn_secondary_style())
        del_btn.clicked.connect(self._remove_merge_item)

        clear_btn = QPushButton("Limpiar Todo")
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.setStyleSheet(self._btn_secondary_style())
        clear_btn.clicked.connect(self.merge_list.clear)

        btn_row.addWidget(add_btn)
        btn_row.addWidget(up_btn)
        btn_row.addWidget(down_btn)
        btn_row.addWidget(del_btn)
        btn_row.addStretch()
        btn_row.addWidget(clear_btn)
        vbox.addLayout(btn_row)

        # Botón Unir
        action_row = QHBoxLayout()
        action_row.addStretch()
        btn_run_merge = QPushButton("📑 Unir y Guardar PDF")
        btn_run_merge.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_run_merge.setFixedHeight(44)
        btn_run_merge.setFixedWidth(240)
        btn_run_merge.setStyleSheet(f"""
            QPushButton {{
                background-color: {self._colors['accent']};
                color: #FFFFFF;
                border: none;
                border-radius: 10px;
                font-size: 11pt;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background-color: {self._colors['accent_hover']};
            }}
        """)
        btn_run_merge.clicked.connect(self._execute_merge)
        action_row.addWidget(btn_run_merge)
        action_row.addStretch()
        vbox.addLayout(action_row)

        return widget

    def _create_split_tab(self) -> QWidget:
        widget = QWidget()
        vbox = QVBoxLayout(widget)
        vbox.setContentsMargins(10, 10, 10, 10)
        vbox.setSpacing(14)

        info = QLabel("Divide documentos extensos o extrae únicamente las páginas que necesitas:")
        info.setStyleSheet(f"color: {self._colors['text_muted']}; font-size: 10pt; font-weight: 600;")
        vbox.addWidget(info)

        # Seleccionar PDF origen
        source_box = QFrame()
        source_box.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors['card']};
                border: 1px solid {self._colors['border']};
                border-radius: 10px;
                padding: 12px;
            }}
        """)
        s_layout = QHBoxLayout(source_box)
        self.split_source_lbl = QLabel("📄 Ningún archivo PDF seleccionado")
        self.split_source_lbl.setStyleSheet(f"color: {self._colors['text_main']}; font-weight: 600; font-size: 10pt;")
        s_layout.addWidget(self.split_source_lbl)
        s_layout.addStretch()

        sel_split_btn = QPushButton("Examinar PDF...")
        sel_split_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        sel_split_btn.setStyleSheet(self._btn_secondary_style())
        sel_split_btn.clicked.connect(self._select_split_file)
        s_layout.addWidget(sel_split_btn)
        vbox.addWidget(source_box)

        # Opciones de división
        opts_box = QFrame()
        opts_box.setStyleSheet(f"""
            QFrame {{
                background-color: {self._colors['card']};
                border: 1px solid {self._colors['border']};
                border-radius: 10px;
                padding: 14px;
            }}
        """)
        o_layout = QVBoxLayout(opts_box)
        o_layout.setSpacing(10)

        self.radio_range = QRadioButton("Extraer rango o páginas específicas")
        self.radio_range.setChecked(True)
        self.radio_range.setStyleSheet(f"color: {self._colors['text_main']}; font-weight: 600; font-size: 10pt;")
        o_layout.addWidget(self.radio_range)

        range_sub = QHBoxLayout()
        range_sub.setContentsMargins(24, 0, 0, 0)
        lbl_ej = QLabel("Páginas (ej: 1-3, 5, 8-10):")
        lbl_ej.setStyleSheet(f"color: {self._colors['text_muted']}; font-size: 9.5pt;")
        self.txt_range = QLineEdit()
        self.txt_range.setPlaceholderText("1-3, 5")
        self.txt_range.setStyleSheet(f"""
            QLineEdit {{
                background-color: {self._colors['bg']};
                border: 1px solid {self._colors['border']};
                border-radius: 6px;
                padding: 6px 10px;
                color: {self._colors['text_main']};
                font-size: 10pt;
            }}
        """)
        range_sub.addWidget(lbl_ej)
        range_sub.addWidget(self.txt_range)
        o_layout.addLayout(range_sub)

        self.radio_each = QRadioButton("Dividir en archivos individuales (1 archivo por página)")
        self.radio_each.setStyleSheet(f"color: {self._colors['text_main']}; font-weight: 600; font-size: 10pt;")
        o_layout.addWidget(self.radio_each)

        vbox.addWidget(opts_box)

        action_row = QHBoxLayout()
        action_row.addStretch()
        btn_run_split = QPushButton("✂️ Ejecutar División")
        btn_run_split.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_run_split.setFixedHeight(44)
        btn_run_split.setFixedWidth(230)
        btn_run_split.setStyleSheet(f"""
            QPushButton {{
                background-color: {self._colors['accent']};
                color: #FFFFFF;
                border: none;
                border-radius: 10px;
                font-size: 11pt;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background-color: {self._colors['accent_hover']};
            }}
        """)
        btn_run_split.clicked.connect(self._execute_split)
        action_row.addWidget(btn_run_split)
        action_row.addStretch()
        vbox.addLayout(action_row)

        self.split_current_file = None
        return widget

    def _btn_secondary_style(self) -> str:
        return f"""
            QPushButton {{
                background-color: {self._colors['bg']};
                color: {self._colors['text_main']};
                border: 1px solid {self._colors['border']};
                border-radius: 8px;
                padding: 6px 14px;
                font-weight: 600;
                font-size: 9.5pt;
            }}
            QPushButton:hover {{
                border-color: {self._colors['accent']};
                background-color: {self._colors['accent_soft']};
                color: {self._colors['accent']};
            }}
        """

    # ── MÉTODOS DE LA PESTAÑA MERGE ──────────────────────────────────────────
    def _add_merge_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Seleccionar PDFs para unir", "", "Archivos PDF (*.pdf)"
        )
        for f in files:
            item = QListWidgetItem(f"📄 {os.path.basename(f)}")
            item.setData(Qt.ItemDataRole.UserRole, f)
            self.merge_list.addItem(item)

    def _move_merge_item_up(self):
        current_row = self.merge_list.currentRow()
        if current_row > 0:
            item = self.merge_list.takeItem(current_row)
            self.merge_list.insertItem(current_row - 1, item)
            self.merge_list.setCurrentRow(current_row - 1)

    def _move_merge_item_down(self):
        current_row = self.merge_list.currentRow()
        if 0 <= current_row < self.merge_list.count() - 1:
            item = self.merge_list.takeItem(current_row)
            self.merge_list.insertItem(current_row + 1, item)
            self.merge_list.setCurrentRow(current_row + 1)

    def _remove_merge_item(self):
        current_row = self.merge_list.currentRow()
        if current_row >= 0:
            self.merge_list.takeItem(current_row)

    def _execute_merge(self):
        paths = []
        for i in range(self.merge_list.count()):
            item = self.merge_list.item(i)
            p = item.data(Qt.ItemDataRole.UserRole)
            if p:
                paths.append(p)

        if len(paths) < 2:
            QMessageBox.warning(self, "Atención", "Agrega al menos 2 archivos PDF para poder unirlos.")
            return

        out_path, _ = QFileDialog.getSaveFileName(
            self, "Guardar PDF Unificado", "documento_unificado.pdf", "Archivos PDF (*.pdf)"
        )
        if not out_path:
            return

        try:
            msg = PDFToolkit.merge_pdfs(paths, out_path)
            QMessageBox.information(self, "Unión Exitosa", f"{msg}\n\nGuardado en:\n{out_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error al unir", f"Ocurrió un error:\n{e}")

    # ── MÉTODOS DE LA PESTAÑA SPLIT ──────────────────────────────────────────
    def _select_split_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar PDF para dividir", "", "Archivos PDF (*.pdf)"
        )
        if path:
            self.split_current_file = path
            self.split_source_lbl.setText(f"📄 {os.path.basename(path)}")

    def _execute_split(self):
        if not self.split_current_file or not os.path.exists(self.split_current_file):
            QMessageBox.warning(self, "Atención", "Por favor selecciona un archivo PDF primero.")
            return

        if self.radio_range.isChecked():
            rng = self.txt_range.text().strip()
            if not rng:
                QMessageBox.warning(self, "Atención", "Ingresa el rango de páginas a extraer (ej: 1-3, 5).")
                return

            base = os.path.splitext(self.split_current_file)[0]
            out_path, _ = QFileDialog.getSaveFileName(
                self, "Guardar PDF Extraído", f"{base}_extraido.pdf", "Archivos PDF (*.pdf)"
            )
            if not out_path:
                return

            try:
                res = PDFToolkit.split_pdf_by_range(self.split_current_file, out_path, rng)
                QMessageBox.information(self, "Extracción Exitosa", f"{res}\n\nGuardado en:\n{out_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error al dividir", str(e))

        else:
            out_dir = QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta de Destino")
            if not out_dir:
                return

            try:
                files = PDFToolkit.split_pdf_each_page(self.split_current_file, out_dir)
                QMessageBox.information(
                    self, "División Exitosa",
                    f"✅ Se dividió el documento en {len(files)} páginas individuales.\n\nCarpeta:\n{out_dir}"
                )
            except Exception as e:
                QMessageBox.critical(self, "Error al dividir", str(e))

    # ── MÉTODOS DE LA PESTAÑA CONVERTER ──────────────────────────────────────
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

        self.drop_icon.setText("📑")
        self.drop_title.setText(f"{name}")
        size_kb = os.path.getsize(file_path) / 1024
        self.drop_subtitle.setText(f"{doc_type} • {size_kb:.1f} KB")

        self.lbl_detected.setText(f"🎯 Archivo detectado: {doc_type}. Elige el formato de salida:")

        for btn in self.target_buttons.values():
            self.pills_layout.removeWidget(btn)
            btn.deleteLater()
        self.target_buttons.clear()

        default_ext = None
        for label, tgt_ext, is_default in targets:
            pill = QPushButton(label)
            pill.setCheckable(True)
            pill.setCursor(Qt.CursorShape.PointingHandCursor)
            pill.setFixedHeight(36)
            pill.setStyleSheet(f"""
                QPushButton {{
                    background-color: {self._colors['card']};
                    color: {self._colors['text_main']};
                    border: 1px solid {self._colors['border']};
                    border-radius: 8px;
                    padding: 4px 14px;
                    font-size: 9.5pt;
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
