import sys
import json
import copy
from datetime import datetime

from PySide6.QtCore import Qt, QSize, QRectF
from PySide6.QtGui import QAction, QFont, QPainter, QPdfWriter, QPageSize, QPixmap
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
    QFrame,
    QGridLayout,
    QScrollArea,
    QSizePolicy,
)

APP_TITLE = "Programa Lista Precios"
DATA_FILE = "lista_precios_data.json"


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


def round_half_up(value: float) -> int:
    base = int(value)
    frac = value - base
    if frac >= 0.5:
        return base + 1
    return base


class PriceListPreview(QWidget):
    def __init__(self):
        super().__init__()
        self.data = copy.deepcopy(DEFAULT_DATA)
        self.setMinimumSize(800, 700)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setStyleSheet("background: #efefef;")

    def set_data(self, data: dict):
        self.data = copy.deepcopy(data)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, False)
        painter.fillRect(self.rect(), Qt.lightGray)

        w = self.width()
        h = self.height()
        margin_x = 60
        y = 55

        title_font = QFont("Arial", 25, QFont.Bold)
        title_font.setItalic(True)
        painter.setFont(title_font)
        painter.drawText(QRectF(0, y, w, 50), Qt.AlignHCenter | Qt.AlignVCenter, self.data["business_name"])

        y += 70
        subtitle_font = QFont("Arial", 18)
        subtitle_font.setItalic(True)
        painter.setFont(subtitle_font)
        painter.drawText(QRectF(0, y, w, 40), Qt.AlignHCenter | Qt.AlignVCenter, self.data["subtitle"])

        y += 65
        table_x = margin_x
        table_w = w - margin_x * 2
        left_col_w = 105
        sub_col_w = (table_w - left_col_w) / 8
        row_h = 38
        header_h = 35

        painter.setFont(QFont("Arial", 12, QFont.Bold))
        painter.drawRect(table_x, y, left_col_w, header_h)
        painter.drawText(QRectF(table_x, y, left_col_w, header_h), Qt.AlignCenter, "METROS")

        groups = ["1 COLOR", "2 COLORES", "3 COLORES", "4 COLORES"]
        for i, group in enumerate(groups):
            gx = table_x + left_col_w + i * sub_col_w * 2
            painter.drawRect(gx, y, sub_col_w * 2, header_h)
            painter.drawText(QRectF(gx, y, sub_col_w * 2, header_h), Qt.AlignCenter, group)

        y2 = y + header_h
        painter.setFont(QFont("Arial", 11))
        painter.drawRect(table_x, y2, left_col_w, header_h)
        for i in range(8):
            cx = table_x + left_col_w + i * sub_col_w
            painter.drawRect(cx, y2, sub_col_w, header_h)
            label = "1 CARA" if i % 2 == 0 else "2 CARAS"
            painter.drawText(QRectF(cx, y2, sub_col_w, header_h), Qt.AlignCenter, label)

        data_y = y2 + header_h
        meters = self.data["meters"]
        columns = self.data["columns"]
        prices = self.data["prices"]

        for row, meter in enumerate(meters):
            ry = data_y + row * row_h
            painter.drawRect(table_x, ry, left_col_w, row_h)
            painter.drawText(QRectF(table_x, ry, left_col_w, row_h), Qt.AlignCenter, str(meter))
            for col, colinfo in enumerate(columns):
                cx = table_x + left_col_w + col * sub_col_w
                painter.drawRect(cx, ry, sub_col_w, row_h)
                val = prices[colinfo["key"]][row]
                text = "" if val == 0 else f"${val}"
                painter.drawText(QRectF(cx, ry, sub_col_w, row_h), Qt.AlignCenter, text)

        confeccion_top = data_y + len(meters) * row_h + 35
        painter.setFont(QFont("Arial", 17))
        painter.drawText(QRectF(0, confeccion_top, w, 30), Qt.AlignHCenter | Qt.AlignVCenter, "CONFECCIÓN:")

        painter.setFont(QFont("Arial", 15))
        confeccion = self.data["confeccion"]
        left_x = w * 0.40
        right_x = w * 0.52
        line_y = confeccion_top + 65
        lines = [
            ("FONDO", f"${confeccion['fondo']} x metro"),
            ("LATERAL", f"${confeccion['lateral']} x metro"),
            ("RIÑON", f"${confeccion['rinon']} c/1000 bolsas"),
            (confeccion["solapa_text"], ""),
        ]
        for idx, (left, right) in enumerate(lines):
            yy = line_y + idx * 38
            painter.drawText(int(left_x), int(yy), left)
            if right:
                painter.drawText(int(right_x), int(yy), right)

        footer_x = w - 150
        footer_y = h - 95
        painter.setFont(QFont("Arial", 15))
        painter.drawText(footer_x, footer_y, f"Lista {self.data['list_number']}")
        painter.drawText(footer_x, footer_y + 35, self.data["date"])


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.resize(1500, 900)
        self.history = []
        self.data = self.load_data()
        self.build_ui()
        self.push_history()
        self.load_data_into_controls()
        self.refresh_preview()

    def build_ui(self):
        self.build_menu()

        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)

        splitter = QSplitter(Qt.Horizontal)
        root.addWidget(splitter)

        preview_container = QWidget()
        preview_layout = QVBoxLayout(preview_container)
        preview_layout.setContentsMargins(10, 10, 10, 10)

        self.preview = PriceListPreview()
        preview_layout.addWidget(self.preview)

        splitter.addWidget(preview_container)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        control_host = QWidget()
        self.control_layout = QVBoxLayout(control_host)
        self.control_layout.setContentsMargins(12, 12, 12, 12)
        self.control_layout.setSpacing(12)
        scroll.setWidget(control_host)

        splitter.addWidget(scroll)
        splitter.setSizes([1000, 430])

        self.build_header_controls()
        self.build_table_editor()
        self.build_confeccion_editor()
        self.build_bulk_actions()
        self.build_bottom_buttons()
        self.control_layout.addStretch()

    def build_menu(self):
        menu = self.menuBar()
        archivo = menu.addMenu("Archivo")

        action_guardar = QAction("Guardar", self)
        action_guardar.triggered.connect(self.save_data)
        archivo.addAction(action_guardar)

        action_pdf = QAction("Exportar PDF", self)
        action_pdf.triggered.connect(self.export_pdf)
        archivo.addAction(action_pdf)

        action_png = QAction("Exportar imagen", self)
        action_png.triggered.connect(self.export_image)
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

        for w in [self.business_name_edit, self.subtitle_edit, self.list_number_edit, self.date_edit]:
            if hasattr(w, "textChanged"):
                w.textChanged.connect(self.on_manual_change)
            if hasattr(w, "valueChanged"):
                w.valueChanged.connect(self.on_manual_change)

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
        row = QHBoxLayout()
        btn_save = QPushButton("Guardar")
        btn_save.clicked.connect(self.save_data)

        btn_pdf = QPushButton("Exportar PDF")
        btn_pdf.clicked.connect(self.export_pdf)

        btn_image = QPushButton("Exportar imagen")
        btn_image.clicked.connect(self.export_image)

        row.addWidget(btn_save)
        row.addWidget(btn_pdf)
        row.addWidget(btn_image)
        self.control_layout.addLayout(row)

    def load_data(self):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return copy.deepcopy(DEFAULT_DATA)
        except Exception:
            return copy.deepcopy(DEFAULT_DATA)

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
        self.data["confeccion"]["solapa_text"] = self.solapa_edit.text().strip()

    def refresh_preview(self):
        self.sync_controls_to_data()
        self.preview.set_data(self.data)

    def on_manual_change(self, *args):
        self.refresh_preview()

    def on_table_item_changed(self, item):
        self.refresh_preview()

    def push_history(self):
        self.history.append(copy.deepcopy(self.data))
        if len(self.history) > 30:
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

    def save_data(self):
        self.sync_controls_to_data()
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            self.push_history()
            QMessageBox.information(self, "Guardado", "Los cambios se guardaron correctamente.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo guardar.\n\n{e}")

    def export_pdf(self):
        self.refresh_preview()
        path, _ = QFileDialog.getSaveFileName(self, "Exportar PDF", "lista_precios.pdf", "PDF (*.pdf)")
        if not path:
            return

        pdf = QPdfWriter(path)
        pdf.setPageSize(QPageSize(QPageSize.A4))
        pdf.setResolution(150)

        painter = QPainter(pdf)
        preview_pixmap = self.preview.grab()
        page_rect = pdf.pageLayout().paintRectPixels(pdf.resolution())
        scaled = preview_pixmap.scaled(page_rect.width(), page_rect.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        x = (page_rect.width() - scaled.width()) // 2
        y = (page_rect.height() - scaled.height()) // 2
        painter.drawPixmap(x, y, scaled)
        painter.end()

        QMessageBox.information(self, "PDF", "PDF exportado correctamente.")

    def export_image(self):
        self.refresh_preview()
        path, _ = QFileDialog.getSaveFileName(self, "Exportar imagen", "lista_precios.png", "PNG (*.png)")
        if not path:
            return
        pixmap = self.preview.grab()
        pixmap.save(path, "PNG")
        QMessageBox.information(self, "Imagen", "Imagen exportada correctamente.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())