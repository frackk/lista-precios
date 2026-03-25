
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
    QPen,
    QColor,
    QImage,
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
        self.setMinimumSize(860, 760)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def set_data(self, data: dict):
        self.data = copy.deepcopy(data)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, False)
        painter.fillRect(self.rect(), QColor("#cfd5dd"))
        margin = 34
        page_rect = self.rect().adjusted(margin, margin, -margin, -margin)
        self.render_page(painter, page_rect)

    def render_page(self, painter: QPainter, page_rect):
        painter.save()
        painter.setRenderHint(QPainter.TextAntialiasing, True)
        painter.fillRect(page_rect, Qt.white)

        grid_pen = QPen(Qt.black)
        grid_pen.setWidth(2)
        grid_pen.setJoinStyle(Qt.MiterJoin)
        painter.setPen(grid_pen)

        x = page_rect.left()
        y = page_rect.top()
        w = page_rect.width()
        h = page_rect.height()

        top_margin = 38
        side_margin = 42

        title_rect = QRectF(x, y + top_margin, w, 38)
        subtitle_rect = QRectF(x, y + top_margin + 46, w, 32)

        painter.setFont(QFont("Arial", 23, QFont.Bold))
        painter.drawText(title_rect, Qt.AlignCenter, self.data["business_name"])

        painter.setFont(QFont("Arial", 15, QFont.Bold))
        painter.drawText(subtitle_rect, Qt.AlignCenter, self.data["subtitle"])

        table_top = y + 132
        table_x = int(x + side_margin)
        table_w = int(w - side_margin * 2)
        left_col_w = 108
        sub_col_w = int((table_w - left_col_w) / 8)
        table_right = table_x + left_col_w + sub_col_w * 8
        header_h1 = 38
        header_h2 = 38
        row_h = 40

        painter.setFont(QFont("Arial", 11, QFont.Bold))

        # Outer table border
        total_table_h = header_h1 + header_h2 + len(self.data["meters"]) * row_h
        painter.drawRect(table_x, int(table_top), table_right - table_x, total_table_h)

        # Vertical lines
        x_positions = [table_x, table_x + left_col_w]
        for i in range(1, 9):
            x_positions.append(table_x + left_col_w + i * sub_col_w)

        for xpos in x_positions[1:-1]:
            # group top row
            if xpos == table_x + left_col_w or xpos == table_x + left_col_w + 2 * sub_col_w or xpos == table_x + left_col_w + 4 * sub_col_w or xpos == table_x + left_col_w + 6 * sub_col_w:
                painter.drawLine(xpos, int(table_top), xpos, int(table_top + total_table_h))
            else:
                painter.drawLine(xpos, int(table_top + header_h1), xpos, int(table_top + total_table_h))

        # Horizontal lines
        painter.drawLine(table_x, int(table_top + header_h1), table_right, int(table_top + header_h1))
        painter.drawLine(table_x, int(table_top + header_h1 + header_h2), table_right, int(table_top + header_h1 + header_h2))
        for i in range(1, len(self.data["meters"])):
            ypos = int(table_top + header_h1 + header_h2 + i * row_h)
            painter.drawLine(table_x, ypos, table_right, ypos)

        # Text headers
        painter.drawText(QRectF(table_x, table_top, left_col_w, header_h1), Qt.AlignCenter, "METROS")
        groups = ["1 COLOR", "2 COLORES", "3 COLORES", "4 COLORES"]
        for i, group in enumerate(groups):
            gx = table_x + left_col_w + i * sub_col_w * 2
            painter.drawText(QRectF(gx, table_top, sub_col_w * 2, header_h1), Qt.AlignCenter, group)

        painter.setFont(QFont("Arial", 10, QFont.Bold))
        for i in range(8):
            cx = table_x + left_col_w + i * sub_col_w
            label = "1 CARA" if i % 2 == 0 else "2 CARAS"
            painter.drawText(QRectF(cx, table_top + header_h1, sub_col_w, header_h2), Qt.AlignCenter, label)

        painter.setFont(QFont("Arial", 10))
        meters = self.data["meters"]
        columns = self.data["columns"]
        prices = self.data["prices"]
        data_y = table_top + header_h1 + header_h2

        for row, meter in enumerate(meters):
            ry = data_y + row * row_h
            painter.drawText(QRectF(table_x, ry, left_col_w, row_h), Qt.AlignCenter, str(meter))
            for col, colinfo in enumerate(columns):
                cx = table_x + left_col_w + col * sub_col_w
                val = prices[colinfo["key"]][row]
                text = "" if val == 0 else f"${val}"
                painter.drawText(QRectF(cx, ry, sub_col_w, row_h), Qt.AlignCenter, text)

        confeccion_top = data_y + len(meters) * row_h + 36
        painter.setFont(QFont("Arial", 16, QFont.Bold))
        painter.drawText(QRectF(x, confeccion_top, w, 28), Qt.AlignCenter, "CONFECCIÓN")

        line_y = confeccion_top + 52
        label_x = x + w * 0.28
        value_x = x + w * 0.48

        confeccion = self.data["confeccion"]
        painter.setFont(QFont("Arial", 13))
        rows = [
            ("FONDO", f"${confeccion['fondo']} x metro"),
            ("LATERAL", f"${confeccion['lateral']} x metro"),
            ("RIÑON", f"${confeccion['rinon']} c/1000 bolsas"),
        ]
        for idx, (left, right) in enumerate(rows):
            yy = line_y + idx * 34
            painter.drawText(QRectF(label_x, yy, 140, 26), Qt.AlignCenter, left)
            painter.drawText(QRectF(value_x, yy, 220, 26), Qt.AlignCenter, right)

        painter.setFont(QFont("Arial", 12, QFont.Bold))
        painter.drawText(QRectF(x, line_y + 112, w, 24), Qt.AlignCenter, confeccion["solapa_text"])

        painter.setFont(QFont("Arial", 12))
        painter.drawText(QRectF(x + w - 170, y + h - 66, 145, 22), Qt.AlignRight, f"Lista {self.data['list_number']}")
        painter.drawText(QRectF(x + w - 170, y + h - 40, 145, 22), Qt.AlignRight, self.data["date"])
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
        self.data = self.load_work_data()
        self.setup_style()
        self.build_ui()
        self.push_history()
        self.load_data_into_controls()
        self.refresh_preview()

    def setup_style(self):
        self.setStyleSheet("""
            QMainWindow {
                background: #1d2128;
            }
            QWidget {
                font-family: Arial;
                font-size: 12px;
                background: #1d2128;
            }
            QSplitter::handle {
                background: #2a303a;
                width: 2px;
            }
            QGroupBox {
                color: #eef2f6;
                border: 1px solid #505866;
                border-radius: 10px;
                margin-top: 12px;
                padding-top: 12px;
                background: #2a303a;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 4px;
                background: transparent;
            }
            QLabel {
                color: #eef2f6;
                background: transparent;
            }
            QLineEdit, QSpinBox, QDoubleSpinBox {
                background: #f5f7fa;
                color: #111111;
                border: 1px solid #bcc5d0;
                border-radius: 6px;
                padding: 5px 6px;
            }
            QTableWidget {
                background: #f5f7fa;
                color: #111111;
                border: 1px solid #bcc5d0;
                border-radius: 6px;
                gridline-color: #ccd3db;
            }
            QTableWidget::item {
                background: #ffffff;
                color: #111111;
                padding: 4px;
            }
            QTableWidget QHeaderView::section {
                background: #e9edf2;
                color: #111111;
                border: 1px solid #bcc5d0;
                padding: 5px;
                font-weight: bold;
            }
            QPushButton {
                background: #f5f7fa;
                color: #111111;
                border: 1px solid #c5cbd3;
                border-radius: 7px;
                padding: 8px 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #ffffff;
            }
            QScrollArea, QScrollArea > QWidget > QWidget {
                border: none;
                background: #1d2128;
            }
            QMenuBar {
                background: #15181d;
                color: white;
            }
            QMenuBar::item:selected {
                background: #2c3340;
            }
            QMenu {
                background: #ffffff;
                color: #111111;
            }
            QMessageBox {
                background: #ffffff;
            }
            QMessageBox QLabel {
                color: #111111;
                background: #ffffff;
                font-size: 13px;
            }
            QMessageBox QPushButton {
                min-width: 90px;
            }
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
        preview_container.setStyleSheet("background: #1d2128;")
        preview_layout = QVBoxLayout(preview_container)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        preview_layout.setSpacing(4)

        self.preview = PriceListPreview()
        preview_layout.addWidget(self.preview, 1)

        signature_row = QHBoxLayout()
        signature_row.setContentsMargins(8, 0, 8, 6)
        signature_row.addStretch()
        self.signature_label = QLabel("Made by Franco Albertario (frack.one)")
        self.signature_label.setStyleSheet("color: #cfd6df; font-size: 12px; background: transparent;")
        signature_row.addWidget(self.signature_label)
        preview_layout.addLayout(signature_row)

        splitter.addWidget(preview_container)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: #1d2128;")

        control_host = QWidget()
        control_host.setStyleSheet("background: #1d2128;")
        self.control_layout = QVBoxLayout(control_host)
        self.control_layout.setContentsMargins(8, 8, 8, 8)
        self.control_layout.setSpacing(12)
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
        menu = self.menuBar()
        archivo = menu.addMenu("Archivo")

        action_guardar = QAction("Guardar paquete", self)
        action_guardar.triggered.connect(self.save_package)
        archivo.addAction(action_guardar)

        action_cargar = QAction("Cargar lista", self)
        action_cargar.triggered.connect(self.load_package)
        archivo.addAction(action_cargar)

        archivo.addSeparator()

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
        self.table.setMinimumHeight(320)

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

        btn_undo = QPushButton("Volver al estado anterior")
        btn_undo.clicked.connect(self.undo_last_change)

        btn_reset = QPushButton("Restaurar valores base")
        btn_reset.clicked.connect(self.restore_defaults)

        grid.addWidget(QLabel("Tabla principal"), 0, 0)
        grid.addWidget(self.global_percent, 0, 1)
        grid.addWidget(btn_global, 0, 2)

        grid.addWidget(QLabel("Confección"), 1, 0)
        grid.addWidget(self.confeccion_percent, 1, 1)
        grid.addWidget(btn_confeccion, 1, 2)

        grid.addWidget(btn_undo, 2, 0, 1, 2)
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

    def refresh_preview(self):
        self.sync_controls_to_data()
        self.preview.set_data(self.data)
        self.save_work_data()

    def on_manual_change(self, *args):
        self.refresh_preview()

    def on_table_item_changed(self, item):
        self.refresh_preview()

    def push_history(self):
        self.history.append(copy.deepcopy(self.data))
        if len(self.history) > 40:
            self.history.pop(0)

    def apply_global_percentage(self):
        self.sync_controls_to_data()
        self.push_history()
        pct = self.global_percent.value() / 100.0
        for colinfo in self.data["columns"]:
            key = colinfo["key"]
            updated = []
            for val in self.data["prices"][key]:
                if val == 0:
                    updated.append(0)
                else:
                    updated.append(round_half_up(val * (1 + pct)))
            self.data["prices"][key] = updated
        self.load_data_into_controls()
        self.refresh_preview()

    def apply_confeccion_percentage(self):
        self.sync_controls_to_data()
        self.push_history()
        pct = self.confeccion_percent.value() / 100.0
        self.data["confeccion"]["fondo"] = round_half_up(self.data["confeccion"]["fondo"] * (1 + pct))
        self.data["confeccion"]["lateral"] = round_half_up(self.data["confeccion"]["lateral"] * (1 + pct))
        self.data["confeccion"]["rinon"] = round_half_up(self.data["confeccion"]["rinon"] * (1 + pct))
        self.load_data_into_controls()
        self.refresh_preview()

    def undo_last_change(self):
        if len(self.history) <= 1:
            QMessageBox.information(self, "Aviso", "No hay un estado anterior para restaurar.")
            return
        self.history.pop()
        self.data = copy.deepcopy(self.history[-1])
        self.load_data_into_controls()
        self.refresh_preview()

    def restore_defaults(self):
        self.push_history()
        self.data = copy.deepcopy(DEFAULT_DATA)
        self.load_data_into_controls()
        self.refresh_preview()

    def make_pdf_file(self, filepath: str):
        pdf = QPdfWriter(filepath)
        pdf.setPageSize(QPageSize(QPageSize.A4))
        pdf.setResolution(150)

        painter = QPainter(pdf)
        page_rect = pdf.pageLayout().paintRectPixels(pdf.resolution())
        margin = 35
        target = QRectF(margin, margin, page_rect.width() - margin * 2, page_rect.height() - margin * 2)
        self.preview.render_page(painter, target)
        painter.end()

    def make_png_file(self, filepath: str):
        image = self.preview.render_to_image(QSize(1600, 2100))
        image.save(filepath, "PNG")

    def export_pdf_dialog(self):
        self.refresh_preview()
        default_name = str(SAVES_DIR / f"{package_base_name(self.data)}.pdf")
        path, _ = QFileDialog.getSaveFileName(self, "Exportar PDF", default_name, "PDF (*.pdf)")
        if not path:
            return
        self.make_pdf_file(path)
        QMessageBox.information(self, "PDF", "El PDF se exportó correctamente.")

    def export_image_dialog(self):
        self.refresh_preview()
        default_name = str(SAVES_DIR / f"{package_base_name(self.data)}.png")
        path, _ = QFileDialog.getSaveFileName(self, "Exportar imagen", default_name, "PNG (*.png)")
        if not path:
            return
        self.make_png_file(path)
        QMessageBox.information(self, "Imagen", "La imagen se exportó correctamente.")

    def save_package(self):
        self.refresh_preview()
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
        if temp_dir.exists():
            try:
                temp_dir.rmdir()
            except Exception:
                pass

        QMessageBox.information(self, "Guardado", "La lista se guardó correctamente.")

    def load_package(self):
        ensure_saves_dir()
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Cargar lista",
            str(SAVES_DIR),
            "Paquete ZIP (*.zip);;JSON (*.json)"
        )
        if not path:
            return

        try:
            if path.lower().endswith(".json"):
                with open(path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
            else:
                loaded = None
                with zipfile.ZipFile(path, "r") as zf:
                    json_candidates = [name for name in zf.namelist() if name.lower().endswith(".json")]
                    if not json_candidates:
                        raise ValueError("El archivo no contiene datos válidos de una lista.")
                    with zf.open(json_candidates[0]) as f:
                        loaded = json.load(f)

            self.push_history()
            self.data = loaded
            self.load_data_into_controls()
            self.refresh_preview()
            QMessageBox.information(self, "Cargado", "La lista se cargó correctamente.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo cargar la lista.\n\n{e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
