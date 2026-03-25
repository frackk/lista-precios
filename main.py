
import sys
import json
import copy
import zipfile
from pathlib import Path

from PySide6.QtCore import Qt, QRectF, QSize
from PySide6.QtGui import (
    QAction,
    QFont,
    QPainter,
    QPdfWriter,
    QPageSize,
    QPageLayout,
    QPen,
    QColor,
    QImage,
    QKeySequence,
)
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QGroupBox,
    QFormLayout,
    QDoubleSpinBox,
    QSpinBox,
    QMessageBox,
    QFileDialog,
    QSplitter,
    QGridLayout,
    QScrollArea,
    QSizePolicy,
    QAbstractItemView,
)
from PySide6.QtPrintSupport import QPrinter, QPrintDialog


APP_TITLE = "Programa Lista Precios"
BASE_DIR = Path(__file__).resolve().parent
SAVES_DIR = BASE_DIR.parent / "lista-precios-saves"
WORK_FILE = SAVES_DIR / "autosave_lista_actual.json"


DEFAULT_DATA = {
    "business_name": "PLASTICOS BROWN",
    "subtitle": "Lista de precios",
    "list_number": 41,
    "date": "01.03.26",
    "meters": [1000, 2000, 3000, 5000, 8000, 10000, 50000],
    "columns": [
        {"key": "1_color_1_cara", "group": "1 COLOR", "label": "1 CARA"},
        {"key": "1_color_2_caras", "group": "1 COLOR", "label": "2 CARAS"},
        {"key": "2_colores_1_cara", "group": "2 COLORES", "label": "1 CARA"},
        {"key": "2_colores_2_caras", "group": "2 COLORES", "label": "2 CARAS"},
        {"key": "3_colores_1_cara", "group": "3 COLORES", "label": "1 CARA"},
        {"key": "3_colores_2_caras", "group": "3 COLORES", "label": "2 CARAS"},
        {"key": "4_colores_1_cara", "group": "4 COLORES", "label": "1 CARA"},
        {"key": "4_colores_2_caras", "group": "4 COLORES", "label": "2 CARAS"},
    ],
    "prices": {
        "1_color_1_cara": [25224, 22885, 21045, 20010, 18515, 16560, 15985],
        "1_color_2_caras": [55493, 54924, 46299, 44022, 40733, 36432, 35167],
        "2_colores_1_cara": [31682, 29785, 28060, 26680, 25070, 24035, 23000],
        "2_colores_2_caras": [69690, 65527, 61732, 58696, 55154, 52877, 50600],
        "3_colores_1_cara": [35995, 34270, 33350, 32430, 31740, 31165, 30130],
        "3_colores_2_caras": [79120, 75394, 73370, 71346, 69805, 68563, 66286],
        "4_colores_1_cara": [0, 51405, 49220, 46460, 44045, 42435, 41055],
        "4_colores_2_caras": [0, 113091, 108284, 102212, 96899, 93357, 90321],
    },
    "confeccion": {
        "fondo": 18700,
        "lateral": 14000,
        "rinon": 2000,
        "solapa_text": "SOLAPA Y ADHESIVO CONSULTAR",
    },
}


def ensure_saves_dir():
    SAVES_DIR.mkdir(parents=True, exist_ok=True)


def round_half_up(value: float) -> int:
    base = int(value)
    frac = value - base
    return base + 1 if frac >= 0.5 else base


def sanitize_filename(text: str) -> str:
    invalid = '<>:"/\\|?*'
    result = "".join("_" if ch in invalid else ch for ch in text)
    return result.strip().replace(" ", "_")


def package_base_name(data: dict) -> str:
    return sanitize_filename(f"Lista_{data['list_number']}")


class PriceListPreview(QWidget):
    def __init__(self):
        super().__init__()
        self.data = copy.deepcopy(DEFAULT_DATA)
        self.setMinimumSize(860, 620)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def set_data(self, data: dict):
        self.data = copy.deepcopy(data)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#d7dbe2"))
        margin = 20
        page_rect = self.rect().adjusted(margin, margin, -margin, -margin)
        self.render_page(painter, page_rect)

    def render_page(self, painter: QPainter, page_rect):
        painter.save()
        painter.fillRect(page_rect, Qt.white)

        x = int(page_rect.left())
        y = int(page_rect.top())
        w = int(page_rect.width())
        h = int(page_rect.height())

        pen = QPen(Qt.black)
        pen.setWidth(2)
        pen.setJoinStyle(Qt.MiterJoin)
        painter.setPen(pen)

        left = x + int(w * 0.02)
        right = x + w - int(w * 0.02)

        title_y = y + int(h * 0.03)
        title_h = int(h * 0.055)
        subtitle_y = title_y + title_h + int(h * 0.02)
        subtitle_h = int(h * 0.04)
        table_top = subtitle_y + subtitle_h + int(h * 0.055)

        table_h = int(h * 0.50)
        header_h1 = int(table_h * 0.12)
        header_h2 = int(table_h * 0.10)
        row_h = int((table_h - header_h1 - header_h2) / len(self.data["meters"]))

        table_x = left
        table_w = right - left
        left_col_w = int(table_w * 0.074)
        sub_col_w = int((table_w - left_col_w) / 8)
        table_right = table_x + left_col_w + sub_col_w * 8

        painter.setFont(QFont("Arial", max(16, int(h * 0.032)), QFont.Bold))
        painter.drawText(QRectF(x, title_y, w, title_h), Qt.AlignCenter, self.data["business_name"])

        painter.setFont(QFont("Arial", max(11, int(h * 0.021)), QFont.Bold))
        painter.drawText(QRectF(x, subtitle_y, w, subtitle_h), Qt.AlignCenter, self.data["subtitle"])

        total_table_h = header_h1 + header_h2 + len(self.data["meters"]) * row_h
        painter.drawRect(table_x, table_top, table_right - table_x, total_table_h)

        x_positions = [table_x, table_x + left_col_w] + [table_x + left_col_w + i * sub_col_w for i in range(1, 9)]
        group_boundaries = {
            table_x + left_col_w,
            table_x + left_col_w + 2 * sub_col_w,
            table_x + left_col_w + 4 * sub_col_w,
            table_x + left_col_w + 6 * sub_col_w,
        }

        for xpos in x_positions[1:-1]:
            if xpos in group_boundaries:
                painter.drawLine(xpos, table_top, xpos, table_top + total_table_h)
            else:
                painter.drawLine(xpos, table_top + header_h1, xpos, table_top + total_table_h)

        painter.drawLine(table_x, table_top + header_h1, table_right, table_top + header_h1)
        painter.drawLine(table_x, table_top + header_h1 + header_h2, table_right, table_top + header_h1 + header_h2)

        for i in range(1, len(self.data["meters"])):
            ypos = table_top + header_h1 + header_h2 + i * row_h
            painter.drawLine(table_x, ypos, table_right, ypos)

        painter.setFont(QFont("Arial", max(8, int(h * 0.017)), QFont.Bold))
        painter.drawText(QRectF(table_x, table_top, left_col_w, header_h1), Qt.AlignCenter, "METROS")
        groups = ["1 COLOR", "2 COLORES", "3 COLORES", "4 COLORES"]
        for i, group in enumerate(groups):
            gx = table_x + left_col_w + i * sub_col_w * 2
            painter.drawText(QRectF(gx, table_top, sub_col_w * 2, header_h1), Qt.AlignCenter, group)

        painter.setFont(QFont("Arial", max(7, int(h * 0.015)), QFont.Bold))
        for i in range(8):
            cx = table_x + left_col_w + i * sub_col_w
            label = "1 CARA" if i % 2 == 0 else "2 CARAS"
            painter.drawText(QRectF(cx, table_top + header_h1, sub_col_w, header_h2), Qt.AlignCenter, label)

        painter.setFont(QFont("Arial", max(8, int(h * 0.017))))
        data_y = table_top + header_h1 + header_h2
        meters = self.data["meters"]
        columns = self.data["columns"]
        prices = self.data["prices"]

        for row, meter in enumerate(meters):
            ry = data_y + row * row_h
            painter.drawText(QRectF(table_x, ry, left_col_w, row_h), Qt.AlignCenter, str(meter))
            for col, colinfo in enumerate(columns):
                cx = table_x + left_col_w + col * sub_col_w
                val = prices[colinfo["key"]][row]
                text = "" if val == 0 else f"${val}"
                painter.drawText(QRectF(cx, ry, sub_col_w, row_h), Qt.AlignCenter, text)

        conf_title_y = table_top + total_table_h + int(h * 0.055)
        painter.setFont(QFont("Arial", max(12, int(h * 0.024)), QFont.Bold))
        painter.drawText(QRectF(x, conf_title_y, w, int(h * 0.04)), Qt.AlignCenter, "CONFECCIÓN")

        rows_y = conf_title_y + int(h * 0.06)
        center_x = x + w // 2
        label_w = int(w * 0.12)
        value_w = int(w * 0.22)
        gap = int(w * 0.02)
        label_x = center_x - label_w - gap // 2
        value_x = center_x + gap // 2
        step = int(h * 0.043)

        painter.setFont(QFont("Arial", max(9, int(h * 0.021))))
        confeccion = self.data["confeccion"]
        rows = [
            ("FONDO", f"${confeccion['fondo']} x metro"),
            ("LATERAL", f"${confeccion['lateral']} x metro"),
            ("RIÑON", f"${confeccion['rinon']} c/1000 bolsas"),
        ]
        for idx, (left_text, right_text) in enumerate(rows):
            yy = rows_y + idx * step
            painter.drawText(QRectF(label_x, yy, label_w, step), Qt.AlignRight | Qt.AlignVCenter, left_text)
            painter.drawText(QRectF(value_x, yy, value_w, step), Qt.AlignLeft | Qt.AlignVCenter, right_text)

        solapa_y = rows_y + step * 3 + int(h * 0.01)
        painter.setFont(QFont("Arial", max(9, int(h * 0.019)), QFont.Bold))
        painter.drawText(QRectF(x, solapa_y, w, int(h * 0.035)), Qt.AlignCenter, confeccion["solapa_text"])

        footer_y = y + h - int(h * 0.05)
        painter.setFont(QFont("Arial", max(8, int(h * 0.016))))
        painter.drawText(QRectF(x + w - 165, footer_y - int(h * 0.028), 145, int(h * 0.024)), Qt.AlignRight, f"Lista {self.data['list_number']}")
        painter.drawText(QRectF(x + w - 165, footer_y, 145, int(h * 0.024)), Qt.AlignRight, self.data["date"])

        painter.restore()

    def render_to_image(self, size: QSize) -> QImage:
        image = QImage(size, QImage.Format_ARGB32)
        image.fill(Qt.white)
        painter = QPainter(image)
        self.render_page(painter, QRectF(0, 0, size.width(), size.height()))
        painter.end()
        return image


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        ensure_saves_dir()
        self.setWindowTitle(APP_TITLE)
        self.resize(1540, 930)
        self.history = []
        self.history_index = -1
        self.is_loading_controls = False
        self.data = self.load_work_data()
        self.setup_style()
        self.build_ui()
        self.load_data_into_controls()
        self.commit_history_state()
        self.refresh_preview(save_history=False)

    def setup_style(self):
        self.setStyleSheet("""
            QMainWindow { background: #252b34; }
            QWidget { font-family: Arial; font-size: 12px; background: #252b34; }
            QSplitter::handle { background: #353d49; width: 2px; }
            QGroupBox {
                color: #eef2f6;
                border: 1px solid #586170;
                border-radius: 10px;
                margin-top: 22px;
                padding-top: 16px;
                background: #313846;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 12px;
                top: -2px;
                padding: 0 6px;
                background: #252b34;
                color: #f4f7fb;
            }
            QLabel { color: #eef2f6; background: transparent; }
            QLineEdit, QSpinBox, QDoubleSpinBox {
                background: #f2f4f7;
                color: #111111;
                border: 1px solid #c2c9d3;
                border-radius: 6px;
                padding: 5px 6px;
                selection-background-color: #a9c7ff;
                selection-color: #111111;
            }
            QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
                background: #ffffff;
                color: #111111;
                border: 1px solid #6ea8fe;
            }
            QTableWidget {
                background: #edf1f5;
                color: #111111;
                border: 1px solid #c2c9d3;
                border-radius: 6px;
                gridline-color: #cdd4dc;
                alternate-background-color: #f8f9fb;
                selection-background-color: #cfe2ff;
                selection-color: #111111;
            }
            QTableWidget::item { background: #ffffff; color: #111111; padding: 4px; }
            QTableWidget::item:selected { background: #cfe2ff; color: #111111; }
            QTableWidget QHeaderView::section {
                background: #dfe5ec;
                color: #111111;
                border: 1px solid #bcc5d0;
                padding: 5px;
                font-weight: bold;
            }
            QPushButton {
                background: #4b5563;
                color: #ffffff;
                border: 1px solid #758090;
                border-radius: 7px;
                padding: 8px 10px;
                font-weight: bold;
            }
            QPushButton:hover { background: #5c6776; color: #ffffff; }
            QPushButton:pressed { background: #3f4854; color: #ffffff; }
            QPushButton:disabled { color: #d1d5db; background: #59616d; }
            QScrollArea, QScrollArea > QWidget > QWidget { border: none; background: #252b34; }
            QMenuBar { background: #1c2128; color: white; }
            QMenuBar::item:selected { background: #343c48; }
            QMenu { background: #ffffff; color: #111111; }
            QMessageBox { background: #ffffff; }
            QMessageBox QLabel { color: #111111; background: #ffffff; font-size: 13px; }
            QMessageBox QPushButton { min-width: 90px; color: #ffffff; }
        """)

    def build_ui(self):
        self.build_menu()

        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(10, 10, 10, 10)

        splitter = QSplitter(Qt.Horizontal)
        root.addWidget(splitter)

        preview_container = QWidget()
        preview_layout = QVBoxLayout(preview_container)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        preview_layout.setSpacing(4)

        self.preview = PriceListPreview()
        preview_layout.addWidget(self.preview, 1)

        signature_row = QHBoxLayout()
        signature_row.setContentsMargins(8, 0, 8, 6)
        signature_row.addStretch()
        self.signature_label = QLabel("Made by Franco Albertario (frack.one)")
        self.signature_label.setStyleSheet("color: #d8dee8; font-size: 12px; background: transparent;")
        signature_row.addWidget(self.signature_label)
        preview_layout.addLayout(signature_row)
        splitter.addWidget(preview_container)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        control_host = QWidget()
        self.control_layout = QVBoxLayout(control_host)
        self.control_layout.setContentsMargins(8, 8, 8, 8)
        self.control_layout.setSpacing(16)
        scroll.setWidget(control_host)
        splitter.addWidget(scroll)

        splitter.setSizes([1030, 470])

        self.build_header_controls()
        self.build_table_editor()
        self.build_confeccion_editor()
        self.build_bulk_actions()
        self.build_bottom_buttons()
        self.control_layout.addStretch()

    def build_menu(self):
        menubar = self.menuBar()

        archivo = menubar.addMenu("Archivo")

        action_guardar = QAction("Guardar paquete", self)
        action_guardar.triggered.connect(self.save_package)
        archivo.addAction(action_guardar)

        action_cargar = QAction("Cargar lista", self)
        action_cargar.triggered.connect(self.load_package)
        archivo.addAction(action_cargar)

        action_pdf = QAction("Exportar PDF", self)
        action_pdf.triggered.connect(self.export_pdf_dialog)
        archivo.addAction(action_pdf)

        action_png = QAction("Exportar imagen", self)
        action_png.triggered.connect(self.export_image_dialog)
        archivo.addAction(action_png)

        archivo.addSeparator()

        action_salir = QAction("Salir", self)
        action_salir.triggered.connect(self.close)
        archivo.addAction(action_salir)

        action_imprimir = QAction("Imprimir", self)
        action_imprimir.setShortcut(QKeySequence.Print)
        action_imprimir.triggered.connect(self.print_list)
        menubar.addAction(action_imprimir)

        action_deshacer = QAction("Deshacer", self)
        action_deshacer.setShortcut(QKeySequence.Undo)
        action_deshacer.triggered.connect(self.undo_action)
        menubar.addAction(action_deshacer)

        action_rehacer = QAction("Rehacer", self)
        action_rehacer.setShortcut(QKeySequence.Redo)
        action_rehacer.triggered.connect(self.redo_action)
        menubar.addAction(action_rehacer)

    def build_header_controls(self):
        box = QGroupBox("Encabezado")
        form = QFormLayout(box)
        self.business_name_edit = QLineEdit()
        self.subtitle_edit = QLineEdit()
        self.list_number_edit = QSpinBox()
        self.list_number_edit.setMaximum(999999)
        self.date_edit = QLineEdit()

        for w in [self.business_name_edit, self.subtitle_edit, self.date_edit]:
            w.textChanged.connect(self.on_manual_change)
        self.list_number_edit.valueChanged.connect(self.on_manual_change)

        form.addRow("Negocio", self.business_name_edit)
        form.addRow("Subtítulo", self.subtitle_edit)
        form.addRow("N° de lista", self.list_number_edit)
        form.addRow("Fecha", self.date_edit)
        self.control_layout.addWidget(box)

    def build_table_editor(self):
        box = QGroupBox("Tabla de precios")
        lay = QVBoxLayout(box)
        self.table = QTableWidget()
        self.table.setRowCount(len(DEFAULT_DATA["meters"]))
        self.table.setColumnCount(1 + len(DEFAULT_DATA["columns"]))
        headers = ["METROS"] + [f"{c['group']}\n{c['label']}" for c in DEFAULT_DATA["columns"]]
        self.table.setHorizontalHeaderLabels(headers)
        self.table.itemChanged.connect(self.on_table_item_changed)
        self.table.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.table.setAlternatingRowColors(True)
        self.table.setMinimumHeight(330)
        lay.addWidget(self.table)
        self.control_layout.addWidget(box)

    def build_confeccion_editor(self):
        box = QGroupBox("Confección")
        form = QFormLayout(box)
        self.fondo_edit = QSpinBox()
        self.fondo_edit.setMaximum(999999999)
        self.lateral_edit = QSpinBox()
        self.lateral_edit.setMaximum(999999999)
        self.rinon_edit = QSpinBox()
        self.rinon_edit.setMaximum(999999999)
        self.solapa_edit = QLineEdit()

        self.fondo_edit.valueChanged.connect(self.on_manual_change)
        self.lateral_edit.valueChanged.connect(self.on_manual_change)
        self.rinon_edit.valueChanged.connect(self.on_manual_change)
        self.solapa_edit.textChanged.connect(self.on_manual_change)

        form.addRow("Fondo", self.fondo_edit)
        form.addRow("Lateral", self.lateral_edit)
        form.addRow("Riñón", self.rinon_edit)
        form.addRow("Texto final", self.solapa_edit)
        self.control_layout.addWidget(box)

    def build_bulk_actions(self):
        box = QGroupBox("Cambios masivos")
        grid = QGridLayout(box)

        self.global_percent = QDoubleSpinBox()
        self.global_percent.setRange(-1000, 1000)
        self.global_percent.setDecimals(2)
        self.global_percent.setSuffix(" %")

        self.confeccion_percent = QDoubleSpinBox()
        self.confeccion_percent.setRange(-1000, 1000)
        self.confeccion_percent.setDecimals(2)
        self.confeccion_percent.setSuffix(" %")

        btn_global = QPushButton("Aplicar a toda la tabla")
        btn_global.clicked.connect(self.apply_global_percentage)

        btn_confeccion = QPushButton("Aplicar a confección")
        btn_confeccion.clicked.connect(self.apply_confeccion_percentage)

        self.btn_undo = QPushButton("Deshacer")
        self.btn_undo.clicked.connect(self.undo_action)

        self.btn_redo = QPushButton("Rehacer")
        self.btn_redo.clicked.connect(self.redo_action)

        btn_reset = QPushButton("Restaurar valores base")
        btn_reset.clicked.connect(self.restore_defaults)

        grid.addWidget(QLabel("Tabla principal"), 0, 0)
        grid.addWidget(self.global_percent, 0, 1)
        grid.addWidget(btn_global, 0, 2)
        grid.addWidget(QLabel("Confección"), 1, 0)
        grid.addWidget(self.confeccion_percent, 1, 1)
        grid.addWidget(btn_confeccion, 1, 2)
        grid.addWidget(self.btn_undo, 2, 0)
        grid.addWidget(self.btn_redo, 2, 1)
        grid.addWidget(btn_reset, 2, 2)
        self.control_layout.addWidget(box)

    def build_bottom_buttons(self):
        row = QGridLayout()
        btn_save = QPushButton("Guardar paquete")
        btn_save.clicked.connect(self.save_package)
        btn_load = QPushButton("Cargar lista")
        btn_load.clicked.connect(self.load_package)
        btn_pdf = QPushButton("Exportar PDF")
        btn_pdf.clicked.connect(self.export_pdf_dialog)
        btn_image = QPushButton("Exportar imagen")
        btn_image.clicked.connect(self.export_image_dialog)

        row.addWidget(btn_save, 0, 0)
        row.addWidget(btn_load, 0, 1)
        row.addWidget(btn_pdf, 1, 0)
        row.addWidget(btn_image, 1, 1)

        wrap = QWidget()
        wrap.setLayout(row)
        wrap.setStyleSheet("background: transparent;")
        self.control_layout.addWidget(wrap)

    def load_work_data(self):
        ensure_saves_dir()
        try:
            with open(WORK_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return copy.deepcopy(DEFAULT_DATA)

    def save_work_data(self):
        self.sync_controls_to_data()
        ensure_saves_dir()
        try:
            with open(WORK_FILE, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def load_data_into_controls(self):
        self.is_loading_controls = True
        self.table.blockSignals(True)

        self.business_name_edit.setText(self.data["business_name"])
        self.subtitle_edit.setText(self.data["subtitle"])
        self.list_number_edit.setValue(self.data["list_number"])
        self.date_edit.setText(self.data["date"])

        meters = self.data["meters"]
        columns = self.data["columns"]
        prices = self.data["prices"]

        for r, meter in enumerate(meters):
            self.table.setItem(r, 0, QTableWidgetItem(str(meter)))
            for c, colinfo in enumerate(columns, start=1):
                val = prices[colinfo["key"]][r]
                text = "" if val == 0 else str(val)
                self.table.setItem(r, c, QTableWidgetItem(text))

        self.fondo_edit.setValue(self.data["confeccion"]["fondo"])
        self.lateral_edit.setValue(self.data["confeccion"]["lateral"])
        self.rinon_edit.setValue(self.data["confeccion"]["rinon"])
        self.solapa_edit.setText(self.data["confeccion"]["solapa_text"])

        self.table.blockSignals(False)
        self.is_loading_controls = False

    def sync_controls_to_data(self):
        self.data["business_name"] = self.business_name_edit.text().strip() or DEFAULT_DATA["business_name"]
        self.data["subtitle"] = self.subtitle_edit.text().strip() or DEFAULT_DATA["subtitle"]
        self.data["list_number"] = self.list_number_edit.value()
        self.data["date"] = self.date_edit.text().strip() or DEFAULT_DATA["date"]

        for r in range(self.table.rowCount()):
            meter_item = self.table.item(r, 0)
            if meter_item:
                try:
                    self.data["meters"][r] = int(meter_item.text())
                except ValueError:
                    pass

        for c, colinfo in enumerate(self.data["columns"], start=1):
            arr = []
            for r in range(self.table.rowCount()):
                item = self.table.item(r, c)
                if not item or not item.text().strip():
                    arr.append(0)
                else:
                    try:
                        arr.append(int(item.text().replace("$", "").strip()))
                    except ValueError:
                        arr.append(0)
            self.data["prices"][colinfo["key"]] = arr

        self.data["confeccion"]["fondo"] = self.fondo_edit.value()
        self.data["confeccion"]["lateral"] = self.lateral_edit.value()
        self.data["confeccion"]["rinon"] = self.rinon_edit.value()
        self.data["confeccion"]["solapa_text"] = self.solapa_edit.text().strip() or DEFAULT_DATA["confeccion"]["solapa_text"]

    def refresh_preview(self, save_history=False):
        if self.is_loading_controls:
            return
        self.sync_controls_to_data()
        self.preview.set_data(self.data)
        self.save_work_data()
        if save_history:
            self.commit_history_state()
        self.update_history_buttons()

    def on_manual_change(self, *args):
        if not self.is_loading_controls:
            self.refresh_preview(save_history=True)

    def on_table_item_changed(self, item):
        if not self.is_loading_controls:
            self.refresh_preview(save_history=True)

    def commit_history_state(self):
        state = copy.deepcopy(self.data)
        if self.history_index >= 0 and self.history and self.history[self.history_index] == state:
            self.update_history_buttons()
            return
        if self.history_index < len(self.history) - 1:
            self.history = self.history[: self.history_index + 1]
        self.history.append(state)
        self.history_index = len(self.history) - 1
        if len(self.history) > 80:
            extra = len(self.history) - 80
            self.history = self.history[extra:]
            self.history_index = len(self.history) - 1
        self.update_history_buttons()

    def update_history_buttons(self):
        if hasattr(self, "btn_undo"):
            self.btn_undo.setEnabled(self.history_index > 0)
        if hasattr(self, "btn_redo"):
            self.btn_redo.setEnabled(self.history_index < len(self.history) - 1)

    def undo_action(self):
        if self.history_index <= 0:
            return
        self.history_index -= 1
        self.data = copy.deepcopy(self.history[self.history_index])
        self.load_data_into_controls()
        self.refresh_preview(save_history=False)

    def redo_action(self):
        if self.history_index >= len(self.history) - 1:
            return
        self.history_index += 1
        self.data = copy.deepcopy(self.history[self.history_index])
        self.load_data_into_controls()
        self.refresh_preview(save_history=False)

    def apply_global_percentage(self):
        self.sync_controls_to_data()
        pct = self.global_percent.value() / 100.0
        for colinfo in self.data["columns"]:
            key = colinfo["key"]
            updated = []
            for val in self.data["prices"][key]:
                updated.append(0 if val == 0 else round_half_up(val * (1 + pct)))
            self.data["prices"][key] = updated
        self.load_data_into_controls()
        self.refresh_preview(save_history=True)

    def apply_confeccion_percentage(self):
        self.sync_controls_to_data()
        pct = self.confeccion_percent.value() / 100.0
        self.data["confeccion"]["fondo"] = round_half_up(self.data["confeccion"]["fondo"] * (1 + pct))
        self.data["confeccion"]["lateral"] = round_half_up(self.data["confeccion"]["lateral"] * (1 + pct))
        self.data["confeccion"]["rinon"] = round_half_up(self.data["confeccion"]["rinon"] * (1 + pct))
        self.load_data_into_controls()
        self.refresh_preview(save_history=True)

    def restore_defaults(self):
        self.data = copy.deepcopy(DEFAULT_DATA)
        self.load_data_into_controls()
        self.refresh_preview(save_history=True)

    def make_pdf_file(self, filepath: str):
        pdf = QPdfWriter(filepath)
        pdf.setPageSize(QPageSize(QPageSize.A4))
        pdf.setPageOrientation(QPageLayout.Landscape)
        pdf.setResolution(150)
        painter = QPainter(pdf)
        page_rect = pdf.pageLayout().paintRectPixels(pdf.resolution())
        margin = 20
        target = QRectF(margin, margin, page_rect.width() - margin * 2, page_rect.height() - margin * 2)
        self.preview.render_page(painter, target)
        painter.end()

    def make_png_file(self, filepath: str):
        image = self.preview.render_to_image(QSize(3508, 2480))
        image.save(filepath, "PNG")

    def export_pdf_dialog(self):
        self.refresh_preview(save_history=False)
        default_name = str(SAVES_DIR / f"{package_base_name(self.data)}.pdf")
        path, _ = QFileDialog.getSaveFileName(self, "Exportar PDF", default_name, "PDF (*.pdf)")
        if path:
            self.make_pdf_file(path)
            QMessageBox.information(self, "PDF", "El PDF se exportó correctamente.")

    def export_image_dialog(self):
        self.refresh_preview(save_history=False)
        default_name = str(SAVES_DIR / f"{package_base_name(self.data)}.png")
        path, _ = QFileDialog.getSaveFileName(self, "Exportar imagen", default_name, "PNG (*.png)")
        if path:
            self.make_png_file(path)
            QMessageBox.information(self, "Imagen", "La imagen se exportó correctamente.")

    def print_list(self):
        self.refresh_preview(save_history=False)
        printer = QPrinter(QPrinter.HighResolution)
        printer.setPageSize(QPageSize(QPageSize.A4))
        printer.setPageOrientation(QPageLayout.Landscape)
        dialog = QPrintDialog(printer, self)
        if dialog.exec():
            painter = QPainter(printer)
            page_rect = printer.pageLayout().paintRectPixels(printer.resolution())
            margin = 20
            target = QRectF(margin, margin, page_rect.width() - margin * 2, page_rect.height() - margin * 2)
            self.preview.render_page(painter, target)
            painter.end()

    def save_package(self):
        self.refresh_preview(save_history=False)
        ensure_saves_dir()
        base = package_base_name(self.data)
        suggested = str(SAVES_DIR / f"{base}.zip")
        path, _ = QFileDialog.getSaveFileName(self, "Guardar paquete", suggested, "Archivo ZIP (*.zip)")
        if not path:
            return

        temp_dir = SAVES_DIR / "_temp_export"
        temp_dir.mkdir(parents=True, exist_ok=True)

        json_path = temp_dir / f"datos_{base}.json"
        pdf_path = temp_dir / f"{base}.pdf"
        png_path = temp_dir / f"{base}.png"

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

        self.make_pdf_file(str(pdf_path))
        self.make_png_file(str(png_path))

        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.write(json_path, arcname=f"{base}/{json_path.name}")
            zf.write(pdf_path, arcname=f"{base}/{pdf_path.name}")
            zf.write(png_path, arcname=f"{base}/{png_path.name}")

        for file in [json_path, pdf_path, png_path]:
            if file.exists():
                file.unlink()
        try:
            temp_dir.rmdir()
        except Exception:
            pass

        QMessageBox.information(self, "Guardado", "La lista se guardó correctamente.")

    def load_package(self):
        ensure_saves_dir()
        path, _ = QFileDialog.getOpenFileName(self, "Cargar lista", str(SAVES_DIR), "Paquete ZIP (*.zip);;JSON (*.json)")
        if not path:
            return

        try:
            if path.lower().endswith(".json"):
                with open(path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
            else:
                with zipfile.ZipFile(path, "r") as zf:
                    json_candidates = sorted([name for name in zf.namelist() if name.lower().endswith(".json")])
                    if not json_candidates:
                        raise ValueError("El archivo no contiene datos válidos de una lista.")
                    with zf.open(json_candidates[0]) as f:
                        loaded = json.load(f)

            self.data = copy.deepcopy(loaded)
            self.load_data_into_controls()
            self.refresh_preview(save_history=True)
            QMessageBox.information(self, "Cargado", "La lista se cargó correctamente.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo cargar la lista.\n\n{e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
